import asyncio
import importlib
import logging
from datetime import datetime
from sqlalchemy import select

from src.core.database import async_session_maker
from src.core.config import get_settings
from src.models import Game, GameStatus, Tick, TickStatus, GameTeam, CheckStatus
from src.services import game_service, scoring_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CheckerWorker:
    def __init__(self):
        self.running = False
        self.settings = get_settings()
        self.checker_modules = {}
    
    async def start(self):
        self.running = True
        logger.info("Checker worker started")
        await self.run_loop()
    
    def stop(self):
        self.running = False
        logger.info("Checker worker stopped")
    
    async def run_loop(self):
        while self.running:
            try:
                await self.process_checks()
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Checker worker error: {e}")
                await asyncio.sleep(10)
    
    async def process_checks(self):
        async with async_session_maker() as db:
            result = await db.execute(
                select(Game).where(Game.status == GameStatus.RUNNING)
            )
            games = list(result.scalars().all())
            
            for game in games:
                if game.current_tick > 0:
                    await self.run_checkers_for_game(db, game)
    
    async def run_checkers_for_game(self, db, game: Game):
        if not game.checker_module:
            return
        
        checker = self.load_checker(game.checker_module)
        if not checker:
            return
        
        result = await db.execute(
            select(Tick).where(
                Tick.game_id == game.id,
                Tick.tick_number == game.current_tick,
            )
        )
        tick = result.scalar_one_or_none()
        if not tick:
            return
        
        game_teams = await game_service.get_game_teams(db, game.id)
        
        for team in game_teams:
            if not team.container_ip:
                continue
            
            try:
                status, sla, message = await self.run_checker(
                    checker, game, team, tick
                )
            except Exception as e:
                status = CheckStatus.ERROR
                sla = 0.0
                message = str(e)
            
            await scoring_service.record_service_status(
                db=db,
                game_id=game.id,
                team_id=team.team_id,
                tick_id=tick.id,
                status=status,
                sla_percentage=sla,
                error_message=message if status == CheckStatus.ERROR else None,
            )
    
    def load_checker(self, module_name: str):
        if module_name in self.checker_modules:
            return self.checker_modules[module_name]
        
        try:
            module = importlib.import_module(module_name)
            self.checker_modules[module_name] = module
            return module
        except ImportError as e:
            logger.error(f"Failed to load checker module {module_name}: {e}")
            return None
    
    async def run_checker(self, checker, game: Game, team: GameTeam, tick: Tick):
        if not hasattr(checker, "check"):
            logger.warning(f"Checker has no 'check' function")
            return CheckStatus.ERROR, 0.0, "Checker missing 'check' function"
        
        result = await asyncio.to_thread(
            checker.check,
            team_ip=team.container_ip,
            game_id=str(game.id),
            team_id=team.team_id,
            tick_number=tick.tick_number,
        )
        
        if isinstance(result, dict):
            status = CheckStatus(result.get("status", "error"))
            sla = result.get("sla", 0.0)
            message = result.get("message")
        elif isinstance(result, bool):
            status = CheckStatus.UP if result else CheckStatus.DOWN
            sla = 100.0 if result else 0.0
            message = None
        else:
            status = CheckStatus.ERROR
            sla = 0.0
            message = "Invalid checker return type"
        
        return status, sla, message


async def main():
    worker = CheckerWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        worker.stop()


if __name__ == "__main__":
    asyncio.run(main())

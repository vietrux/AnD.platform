import asyncio
import logging
from datetime import datetime
from sqlalchemy import select

from src.core.database import async_session_maker, wait_for_db
from src.core.config import get_settings
from src.models import Game, GameStatus, Tick, TickStatus, FlagType, GameTeam
from src.services import game_service, flag_service, docker_service, scoring_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_FLAG_PATH = "/home/ctf/flag1.txt"
ROOT_FLAG_PATH = "/root/flag2.txt"


class TickWorker:
    def __init__(self):
        self.running = False
        self.settings = get_settings()
    
    async def start(self):
        self.running = True
        logger.info("Tick worker started")
        await wait_for_db()
        await self.run_loop()
    
    def stop(self):
        self.running = False
        logger.info("Tick worker stopped")
    
    async def run_loop(self):
        while self.running:
            try:
                await self.process_running_games()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Tick worker error: {e}")
                await asyncio.sleep(5)
    
    async def process_running_games(self):
        async with async_session_maker() as db:
            result = await db.execute(
                select(Game).where(Game.status == GameStatus.RUNNING)
            )
            games = list(result.scalars().all())
            
            for game in games:
                await self.process_game_tick(db, game)
    
    async def process_game_tick(self, db, game: Game):
        now = datetime.utcnow()
        
        if game.start_time is None:
            return
        
        elapsed = (now - game.start_time).total_seconds()
        expected_tick = int(elapsed / game.tick_duration_seconds) + 1
        
        if expected_tick > game.current_tick:
            await self.execute_tick(db, game, expected_tick)
    
    async def execute_tick(self, db, game: Game, tick_number: int):
        # Check if tick already exists for this game/tick_number
        existing_tick = await db.execute(
            select(Tick).where(
                Tick.game_id == game.id,
                Tick.tick_number == tick_number,
            )
        )
        if existing_tick.scalar_one_or_none():
            # Tick already created, skip
            return
        
        logger.info(f"Game {game.name}: Starting tick {tick_number}")
        
        tick = Tick(
            game_id=game.id,
            tick_number=tick_number,
            status=TickStatus.ACTIVE,
            start_time=datetime.utcnow(),
        )
        db.add(tick)
        await db.commit()
        await db.refresh(tick)
        
        game_teams = await game_service.get_game_teams(db, game.id)
        flags_placed = 0
        
        for team in game_teams:
            user_flag = await flag_service.create_flag(
                db, game.id, team.team_id, tick, FlagType.USER
            )
            root_flag = await flag_service.create_flag(
                db, game.id, team.team_id, tick, FlagType.ROOT
            )
            
            if team.container_name:
                await docker_service.inject_flag_to_container(
                    team.container_name, user_flag.flag_value, USER_FLAG_PATH
                )
                await docker_service.inject_flag_to_container(
                    team.container_name, root_flag.flag_value, ROOT_FLAG_PATH
                )
            
            flags_placed += 2
        
        tick.flags_placed = flags_placed
        tick.status = TickStatus.COMPLETED
        tick.end_time = datetime.utcnow()
        
        game.current_tick = tick_number
        
        await db.commit()
        
        await scoring_service.update_rankings(db, game.id)
        
        logger.info(f"Game {game.name}: Tick {tick_number} complete, {flags_placed} flags placed")
        
        await self.check_auto_stop(db, game, tick_number)
    
    async def check_auto_stop(self, db, game: Game, tick_number: int):
        if game.max_ticks is not None and tick_number >= game.max_ticks:
            logger.info(f"Game {game.name}: Reached max_ticks ({game.max_ticks}), auto-stopping")
            
            game_teams = await game_service.get_game_teams(db, game.id)
            for team in game_teams:
                if team.container_name:
                    await docker_service.stop_team_container(team.container_name)
            
            await game_service.update_game_status(db, game, GameStatus.FINISHED)


async def main():
    worker = TickWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        worker.stop()


if __name__ == "__main__":
    asyncio.run(main())

"""
Tick Manager
Main controller orchestrating competition rounds
"""

import time
import logging
from datetime import datetime, timedelta
from django.utils import timezone

from gameserver.config import game_config
from gameserver.models import Tick
from .flag_coordinator import FlagCoordinator

logger = logging.getLogger(__name__)


class TickManager:
    """
    Main tick/round manager
    Orchestrates the competition lifecycle
    """
    
    def __init__(self):
        self.running = False
        self.current_tick = None
        self.flag_coordinator = FlagCoordinator()
        logger.info("TickManager initialized")
    
    def start(self):
        """Start the tick loop"""
        self.running = True
        logger.info("Starting tick loop")
        self.run_loop()
    
    def stop(self):
        """Stop the tick loop"""
        self.running = False
        logger.info("Stopping tick loop")
    
    def run_loop(self):
        """
        Main tick loop
        Runs every TICK_DURATION_SECONDS
        """
        tick_number = self._get_next_tick_number()
        
        while self.running:
            try:
                # Create and start new tick
                tick = self._create_tick(tick_number)
                self.current_tick = tick
                
                logger.info(f"=== Starting Tick {tick_number} ===")
                tick.start()
                
                # Execute tick phases
                self._execute_tick(tick)
                
                # Complete tick
                tick.complete()
                logger.info(f"=== Completed Tick {tick_number} in {tick.actual_duration}s ===")
                
                # Increment for next tick
                tick_number += 1
                
                # Sleep until next tick
                self._sleep_until_next_tick(tick)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping...")
                self.stop()
                break
            except Exception as e:
                logger.error(f"Error in tick {tick_number}: {e}", exc_info=True)
                if self.current_tick:
                    self.current_tick.mark_error()
                time.sleep(5)  # Brief pause before retry
    
    def _create_tick(self, tick_number):
        """Create a new tick object"""
        tick = Tick.objects.create(
            tick_number=tick_number,
            start_time=timezone.now(),
            duration_seconds=game_config.TICK_DURATION_SECONDS,
            status=Tick.STATUS_PENDING
        )
        return tick
    
    def _execute_tick(self, tick):
        """
        Execute all tick phases
        1. Generate and place flags
        2. Schedule checkers
        3. Calculate scores
        """
        # Phase 1: Generate and place flags
        logger.info(f"Tick {tick.tick_number}: Generating flags...")
        flags_placed = self.flag_coordinator.generate_and_place_flags(tick)
        tick.flags_placed = flags_placed
        tick.save(update_fields=['flags_placed'])
        
        # Phase 2: Schedule checker tasks (will be done via Celery)
        logger.info(f"Tick {tick.tick_number}: Scheduling checkers...")
        # TODO: Implement checker scheduling
        
        # Phase 3: Score calculation will happen after checkers complete
        logger.info(f"Tick {tick.tick_number}: Tick execution complete")
    
    def _get_next_tick_number(self):
        """Get the next tick number to use"""
        latest_tick = Tick.get_latest_tick()
        if latest_tick:
            return latest_tick.tick_number + 1
        return 1
    
    def _sleep_until_next_tick(self, tick):
        """Sleep until it's time for the next tick"""
        if not tick.start_time:
            time.sleep(game_config.TICK_DURATION_SECONDS)
            return
        
        elapsed = (timezone.now() - tick.start_time).total_seconds()
        remaining = max(0, game_config.TICK_DURATION_SECONDS - elapsed)
        
        if remaining > 0:
            logger.debug(f"Sleeping for {remaining:.1f}s until next tick")
            time.sleep(remaining)


def main():
    """Entry point when run as module"""
    import django
    django.setup()
    
    manager = TickManager()
    try:
        manager.start()
    except KeyboardInterrupt:
        manager.stop()


if __name__ == "__main__":
    main()

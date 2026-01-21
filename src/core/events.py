"""
WebSocket Event Manager for Real-time Updates.

Uses PostgreSQL LISTEN/NOTIFY to detect database changes and broadcast
to connected WebSocket clients.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Callable, Any
from contextlib import asynccontextmanager

import asyncpg

from src.core.config import get_settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections grouped by game_id."""
    
    def __init__(self):
        # game_id -> set of (websocket, send_func) tuples
        self.active_connections: Dict[str, Set] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, game_id: str, websocket: Any) -> None:
        """Add a WebSocket connection for a specific game."""
        async with self._lock:
            if game_id not in self.active_connections:
                self.active_connections[game_id] = set()
            self.active_connections[game_id].add(websocket)
            logger.info(f"WebSocket connected for game {game_id}. Total: {len(self.active_connections[game_id])}")
    
    async def disconnect(self, game_id: str, websocket: Any) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if game_id in self.active_connections:
                self.active_connections[game_id].discard(websocket)
                if not self.active_connections[game_id]:
                    del self.active_connections[game_id]
                logger.info(f"WebSocket disconnected from game {game_id}")
    
    async def broadcast_to_game(self, game_id: str, message: dict) -> None:
        """Send a message to all connections for a specific game."""
        async with self._lock:
            connections = self.active_connections.get(game_id, set()).copy()
        
        if not connections:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for websocket in connections:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            await self.disconnect(game_id, ws)
    
    async def broadcast_all(self, message: dict) -> None:
        """Broadcast message to all connected clients."""
        async with self._lock:
            all_game_ids = list(self.active_connections.keys())
        
        for game_id in all_game_ids:
            await self.broadcast_to_game(game_id, message)
    
    def get_connection_count(self, game_id: str = None) -> int:
        """Get number of active connections."""
        if game_id:
            return len(self.active_connections.get(game_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
connection_manager = ConnectionManager()


class PostgresEventListener:
    """Listens to PostgreSQL NOTIFY events and triggers callbacks."""
    
    def __init__(self, database_url: str):
        # Convert async URL to sync for asyncpg
        self.database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        self.connection: asyncpg.Connection | None = None
        self.running = False
        self._callbacks: Dict[str, list[Callable]] = {}
    
    def on_event(self, channel: str, callback: Callable[[dict], Any]) -> None:
        """Register a callback for a specific channel."""
        if channel not in self._callbacks:
            self._callbacks[channel] = []
        self._callbacks[channel].append(callback)
    
    async def _handle_notification(self, connection, pid, channel: str, payload: str) -> None:
        """Handle incoming PostgreSQL notification."""
        try:
            data = json.loads(payload)
            logger.debug(f"Received notification on {channel}: {data}")
            
            callbacks = self._callbacks.get(channel, [])
            for callback in callbacks:
                try:
                    result = callback(data)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Callback error for {channel}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in notification: {e}")
    
    async def start(self) -> None:
        """Start listening for PostgreSQL events."""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting PostgreSQL event listener...")
        
        try:
            self.connection = await asyncpg.connect(self.database_url)
            
            # Add listener for each registered channel
            for channel in self._callbacks.keys():
                await self.connection.add_listener(channel, self._handle_notification)
                logger.info(f"Listening on channel: {channel}")
            
            # Keep connection alive
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"PostgreSQL listener error: {e}")
            self.running = False
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the event listener."""
        self.running = False
        if self.connection:
            try:
                for channel in self._callbacks.keys():
                    await self.connection.remove_listener(channel, self._handle_notification)
                await self.connection.close()
            except Exception as e:
                logger.warning(f"Error closing listener connection: {e}")
            finally:
                self.connection = None
        logger.info("PostgreSQL event listener stopped")


# Global event listener instance (initialized on startup)
event_listener: PostgresEventListener | None = None


async def handle_scoreboard_update(data: dict) -> None:
    """Handle scoreboard update notification from PostgreSQL."""
    game_id = data.get("game_id")
    if not game_id:
        return
    
    logger.info(f"Scoreboard updated for game {game_id}")
    
    # Notify all connected clients for this game to refresh
    await connection_manager.broadcast_to_game(
        str(game_id),
        {
            "type": "scoreboard_update",
            "game_id": str(game_id),
            "team_id": data.get("team_id"),
            "operation": data.get("operation"),
            "timestamp": data.get("timestamp"),
        }
    )


async def init_event_listener() -> None:
    """Initialize and start the PostgreSQL event listener."""
    global event_listener
    
    settings = get_settings()
    event_listener = PostgresEventListener(settings.database_url)
    
    # Register scoreboard update handler
    event_listener.on_event("scoreboard_updated", handle_scoreboard_update)
    
    # Start listener in background task
    asyncio.create_task(event_listener.start())
    logger.info("Event listener initialized")


async def shutdown_event_listener() -> None:
    """Shutdown the event listener gracefully."""
    global event_listener
    if event_listener:
        await event_listener.stop()
        event_listener = None
    
    # Also stop tick timer manager
    await tick_timer_manager.stop_all()


# =============================================================================
# TICK TIMER MANAGER
# =============================================================================

from dataclasses import dataclass
from datetime import datetime


@dataclass
class GameTickInfo:
    """Stores tick timing information for a running game."""
    game_id: str
    current_tick: int
    tick_duration_seconds: int
    tick_started_at: datetime
    game_status: str  # running, paused, finished


class TickTimerManager:
    """
    Manages tick timer broadcasts for running games.
    
    When a game is registered, starts a background task that broadcasts
    tick progress every second to all connected WebSocket clients.
    """
    
    def __init__(self):
        self._games: Dict[str, GameTickInfo] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
    
    async def register_game(
        self,
        game_id: str,
        current_tick: int,
        tick_duration_seconds: int,
        tick_started_at: datetime,
        game_status: str = "running",
    ) -> None:
        """Register a game for tick timer broadcasts."""
        async with self._lock:
            self._games[game_id] = GameTickInfo(
                game_id=game_id,
                current_tick=current_tick,
                tick_duration_seconds=tick_duration_seconds,
                tick_started_at=tick_started_at,
                game_status=game_status,
            )
            
            # Start broadcast task if not already running
            if game_id not in self._tasks or self._tasks[game_id].done():
                self._tasks[game_id] = asyncio.create_task(
                    self._broadcast_loop(game_id)
                )
                logger.info(f"Started tick timer broadcast for game {game_id}")
    
    async def update_tick(
        self,
        game_id: str,
        current_tick: int,
        tick_started_at: datetime,
    ) -> None:
        """Update tick information when a new tick starts."""
        async with self._lock:
            if game_id in self._games:
                self._games[game_id].current_tick = current_tick
                self._games[game_id].tick_started_at = tick_started_at
                logger.debug(f"Updated tick info for game {game_id}: tick {current_tick}")
    
    async def update_status(self, game_id: str, status: str) -> None:
        """Update game status (running, paused, finished)."""
        async with self._lock:
            if game_id in self._games:
                self._games[game_id].game_status = status
                logger.info(f"Game {game_id} status changed to {status}")
                
                # If finished, stop the broadcast task
                if status == "finished":
                    await self._stop_game_task(game_id)
    
    async def unregister_game(self, game_id: str) -> None:
        """Stop tracking a game."""
        async with self._lock:
            await self._stop_game_task(game_id)
            self._games.pop(game_id, None)
            logger.info(f"Unregistered game {game_id} from tick timer")
    
    async def _stop_game_task(self, game_id: str) -> None:
        """Stop the broadcast task for a game (must be called with lock held)."""
        if game_id in self._tasks:
            task = self._tasks.pop(game_id)
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    async def stop_all(self) -> None:
        """Stop all broadcast tasks."""
        async with self._lock:
            for game_id in list(self._tasks.keys()):
                await self._stop_game_task(game_id)
            self._games.clear()
            logger.info("Stopped all tick timer broadcasts")
    
    async def _broadcast_loop(self, game_id: str) -> None:
        """Background task that broadcasts tick timer every second."""
        try:
            while True:
                async with self._lock:
                    game_info = self._games.get(game_id)
                
                if not game_info:
                    break
                
                # Calculate timing
                now = datetime.utcnow()
                elapsed = (now - game_info.tick_started_at).total_seconds()
                elapsed = max(0, elapsed)  # Ensure non-negative
                remaining = max(0, game_info.tick_duration_seconds - elapsed)
                
                # Build message
                message = {
                    "type": "tick_timer",
                    "game_id": game_info.game_id,
                    "current_tick": game_info.current_tick,
                    "tick_duration_seconds": game_info.tick_duration_seconds,
                    "seconds_elapsed": int(elapsed),
                    "seconds_remaining": int(remaining),
                    "progress_percent": min(100, int((elapsed / game_info.tick_duration_seconds) * 100)),
                    "tick_started_at": game_info.tick_started_at.isoformat() + "Z",
                    "game_status": game_info.game_status,
                    "server_time": now.isoformat() + "Z",
                }
                
                # Broadcast to all connected clients for this game
                await connection_manager.broadcast_to_game(game_id, message)
                
                # Wait 1 second before next broadcast
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.debug(f"Tick timer broadcast cancelled for game {game_id}")
        except Exception as e:
            logger.error(f"Error in tick timer broadcast for game {game_id}: {e}")
    
    def get_game_info(self, game_id: str) -> GameTickInfo | None:
        """Get current game tick info (for initial WebSocket connection)."""
        return self._games.get(game_id)


# Global tick timer manager instance
tick_timer_manager = TickTimerManager()

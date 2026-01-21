"""
WebSocket Routes for Real-time Updates.

Provides WebSocket endpoints for:
- Real-time scoreboard updates
- Live tick timer (seconds remaining in current tick)
- Game state changes (pause/resume/stop)

All endpoints are PUBLIC (no authentication required).
"""

import logging
import uuid as uuid_module
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.database import get_db
from src.core.events import connection_manager, tick_timer_manager
from src.services import scoring_service, game_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/game/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: str):
    """
    Combined WebSocket endpoint for all real-time game updates.
    
    PUBLIC - No authentication required.
    
    On connection, sends:
    - Initial game state (status, tick info)
    - Current scoreboard
    
    Ongoing broadcasts (every second):
    - tick_timer: current tick, seconds elapsed/remaining, progress %
    
    Event broadcasts:
    - scoreboard_update: when scores change
    - tick_change: when a new tick starts
    - game_state: when game pauses/resumes/stops
    """
    await websocket.accept()
    logger.info(f"Game WebSocket connection for game {game_id}")
    
    # Validate game_id format
    try:
        game_uuid = uuid_module.UUID(game_id)
    except ValueError:
        await websocket.send_json({
            "type": "error",
            "message": "Invalid game ID format"
        })
        await websocket.close()
        return
    
    # Register connection
    await connection_manager.connect(game_id, websocket)
    
    try:
        # Fetch game info and send initial state
        async for db in get_db():
            try:
                game = await game_service.get_game(db, game_uuid)
                
                if not game:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Game not found"
                    })
                    break
                
                # Send initial game state
                tick_started_at = game.current_tick_started_at or game.start_time
                now = datetime.utcnow()
                
                if tick_started_at and game.status.value == "running":
                    elapsed = (now - tick_started_at).total_seconds()
                    remaining = max(0, game.tick_duration_seconds - elapsed)
                else:
                    elapsed = 0
                    remaining = game.tick_duration_seconds
                
                await websocket.send_json({
                    "type": "initial",
                    "game_id": game_id,
                    "game_name": game.name,
                    "game_status": game.status.value,
                    "current_tick": game.current_tick,
                    "max_ticks": game.max_ticks,
                    "tick_duration_seconds": game.tick_duration_seconds,
                    "seconds_elapsed": int(elapsed),
                    "seconds_remaining": int(remaining),
                    "server_time": now.isoformat() + "Z",
                })
                
                # Send current scoreboard
                scoreboard_data = await scoring_service.get_scoreboard(db, game_uuid)
                if scoreboard_data:
                    await websocket.send_json({
                        "type": "scoreboard",
                        "game_id": game_id,
                        "entries": [
                            {
                                "team_id": s.team_id,
                                "attack_points": s.attack_points,
                                "defense_points": s.defense_points,
                                "sla_points": s.sla_points,
                                "total_points": s.total_points,
                                "rank": s.rank,
                                "flags_captured": s.flags_captured,
                                "flags_lost": s.flags_lost,
                            }
                            for s in scoreboard_data
                        ]
                    })
                
                # Register game for tick timer broadcasts if running
                if game.status.value == "running" and tick_started_at:
                    await tick_timer_manager.register_game(
                        game_id=game_id,
                        current_tick=game.current_tick,
                        tick_duration_seconds=game.tick_duration_seconds,
                        tick_started_at=tick_started_at,
                        game_status=game.status.value,
                    )
                
            except Exception as e:
                logger.error(f"Error sending initial game state: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Failed to fetch game data"
                })
            break
        
        # Keep connection alive and handle client messages
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
                elif data == "refresh":
                    # Client requests fresh scoreboard
                    async for db in get_db():
                        try:
                            scoreboard_data = await scoring_service.get_scoreboard(db, game_uuid)
                            if scoreboard_data:
                                await websocket.send_json({
                                    "type": "scoreboard",
                                    "game_id": game_id,
                                    "entries": [
                                        {
                                            "team_id": s.team_id,
                                            "attack_points": s.attack_points,
                                            "defense_points": s.defense_points,
                                            "sla_points": s.sla_points,
                                            "total_points": s.total_points,
                                            "rank": s.rank,
                                            "flags_captured": s.flags_captured,
                                            "flags_lost": s.flags_lost,
                                        }
                                        for s in scoreboard_data
                                    ]
                                })
                        except Exception as e:
                            logger.error(f"Error refreshing scoreboard: {e}")
                        break
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info(f"Game WebSocket disconnected for game {game_id}")
    except Exception as e:
        logger.error(f"Game WebSocket error for game {game_id}: {e}")
    finally:
        await connection_manager.disconnect(game_id, websocket)


@router.websocket("/ws/scoreboard/{game_id}")
async def scoreboard_websocket(websocket: WebSocket, game_id: str):
    """
    Legacy WebSocket endpoint for scoreboard updates only.
    
    Use /ws/game/{game_id} for combined updates including tick timer.
    """
    await websocket.accept()
    logger.info(f"Scoreboard WebSocket connection for game {game_id}")
    
    # Register connection
    await connection_manager.connect(game_id, websocket)
    
    try:
        # Send initial scoreboard data
        async for db in get_db():
            try:
                game_uuid = uuid_module.UUID(game_id)
                scoreboard_data = await scoring_service.get_scoreboard(db, game_uuid)
                if scoreboard_data:
                    await websocket.send_json({
                        "type": "initial",
                        "game_id": game_id,
                        "entries": [
                            {
                                "team_id": s.team_id,
                                "attack_points": s.attack_points,
                                "defense_points": s.defense_points,
                                "sla_points": s.sla_points,
                                "total_points": s.total_points,
                                "rank": s.rank,
                                "flags_captured": s.flags_captured,
                                "flags_lost": s.flags_lost,
                            }
                            for s in scoreboard_data
                        ]
                    })
            except Exception as e:
                logger.error(f"Error fetching initial scoreboard: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Failed to fetch scoreboard"
                })
            break
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info(f"Scoreboard WebSocket disconnected for game {game_id}")
    except Exception as e:
        logger.error(f"Scoreboard WebSocket error for game {game_id}: {e}")
    finally:
        await connection_manager.disconnect(game_id, websocket)


@router.websocket("/ws/health")
async def health_websocket(websocket: WebSocket):
    """Simple WebSocket health check endpoint."""
    await websocket.accept()
    await websocket.send_json({"status": "connected"})
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass

"""
WebSocket endpoint for real-time trip sync and presence.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
from app.core.postgres import get_db
from app.core.clerk import verify_clerk_token
from app.models.user import User
from app.models.collaborator import TripCollaborator, CollaboratorStatus
from app.models.trip import Trip
import json
import asyncio
import logging
import jwt

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


# ── Connection Manager ──────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        # trip_id → set of WebSocket connections
        self.active: dict[int, set[WebSocket]] = {}
        # trip_id → {clerk_id: display_name}
        self.presence: dict[int, dict[str, str]] = {}
        # websocket → (trip_id, clerk_id)  for cleanup on disconnect
        self.meta: dict[WebSocket, tuple[int, str]] = {}

    async def connect(self, websocket: WebSocket, trip_id: int, clerk_id: str, display_name: str):
        await websocket.accept()
        self.active.setdefault(trip_id, set()).add(websocket)
        self.presence.setdefault(trip_id, {})[clerk_id] = display_name
        self.meta[websocket] = (trip_id, clerk_id)
        logger.info(f"🔌 WS connect: user={clerk_id} trip={trip_id}")

    def disconnect(self, websocket: WebSocket):
        if websocket not in self.meta:
            return
        trip_id, clerk_id = self.meta.pop(websocket)
        self.active.get(trip_id, set()).discard(websocket)
        if trip_id in self.presence:
            self.presence[trip_id].pop(clerk_id, None)
        logger.info(f"🔌 WS disconnect: user={clerk_id} trip={trip_id}")

    async def broadcast(self, trip_id: int, message: dict, exclude: WebSocket | None = None):
        """Broadcast JSON message to all connections on a trip."""
        conns = self.active.get(trip_id, set()).copy()
        dead = set()
        for ws in conns:
            if ws is exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws)

    def get_presence(self, trip_id: int) -> list[str]:
        """Return list of display names currently viewing a trip."""
        return list(self.presence.get(trip_id, {}).values())


# Singleton — imported by planner.py and collaborators.py
manager = ConnectionManager()


# ── WS Auth helper ──────────────────────────────────────────────────
async def get_ws_user(token: str, db: Session) -> User | None:
    """Verify Clerk JWT from query param and return User."""
    try:
        payload = await verify_clerk_token(token)
        clerk_id = payload.get("sub")
        if not clerk_id:
            return None
        return db.query(User).filter(User.clerk_id == clerk_id).first()
    except (jwt.InvalidTokenError, Exception):
        return None


async def verify_trip_access_ws(trip_id: int, user: User, db: Session) -> bool:
    """Return True if user is owner or accepted collaborator."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        return False
    if trip.user_id == user.id:
        return True
    collab = db.query(TripCollaborator).filter(
        TripCollaborator.trip_id == trip_id,
        TripCollaborator.clerk_user_id == user.clerk_id,
        TripCollaborator.status == CollaboratorStatus.ACCEPTED,
    ).first()
    return collab is not None


# ── WS Endpoint ─────────────────────────────────────────────────────
@router.websocket("/ws/trips/{trip_id}")
async def trip_websocket(
    websocket: WebSocket,
    trip_id: int,
    token: str = Query(..., description="Clerk JWT for auth"),
    db: Session = Depends(get_db),
):
    # Auth
    user = await get_ws_user(token, db)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # Access check
    has_access = await verify_trip_access_ws(trip_id, user, db)
    if not has_access:
        await websocket.close(code=4003, reason="Forbidden")
        return

    display_name = user.name or user.email or "Someone"

    # Connect and broadcast join presence
    await manager.connect(websocket, trip_id, user.clerk_id, display_name)
    await manager.broadcast(trip_id, {
        "type": "presence_join",
        "payload": {
            "clerk_id": user.clerk_id,
            "display_name": display_name,
            "viewers": manager.get_presence(trip_id),
        }
    })

    try:
        while True:
            # Keep connection alive — client sends pings, we echo pong
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(trip_id, {
            "type": "presence_leave",
            "payload": {
                "clerk_id": user.clerk_id,
                "display_name": display_name,
                "viewers": manager.get_presence(trip_id),
            }
        })

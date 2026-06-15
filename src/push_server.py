import asyncio
import json
import logging
import random
import time
from typing import Any, Callable, Awaitable

import websockets
from websockets.asyncio.server import Server, ServerConnection

logger = logging.getLogger(__name__)


class PushServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 10086):
        self._host = host
        self._port = port
        self._clients: set[ServerConnection] = set()
        self._server: Server | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._last_touch: dict[str, Any] | None = None
        self._touch_handler: Callable[[str], Awaitable[None]] | None = None
        self._client_mode = False
        self._client_ws = None
        self._client_logs: list[str] = []

    def set_touch_handler(self, handler: Callable[[str], Awaitable[None]]) -> None:
        """Set callback for touch events: handler(area) -> None"""
        self._touch_handler = handler

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        try:
            self._server = await websockets.serve(
                self._handler,
                self._host,
                self._port,
            )
            logger.info("PushServer listening on ws://%s:%s", self._host, self._port)
        except OSError as e:
            if e.errno == 98:  # Address already in use
                logger.info("Port %s in use, connecting as client", self._port)
                self._client_mode = True
                await self._connect_as_client()
            else:
                raise

    async def _connect_as_client(self) -> None:
        uri = f"ws://{self._host}:{self._port}"
        self._client_ws = await websockets.connect(uri)
        logger.info("PushServer connected as client to %s", uri)

    async def stop(self) -> None:
        if self._client_ws:
            await self._client_ws.close()
            self._client_ws = None
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        for ws in list(self._clients):
            await ws.close()
        self._clients.clear()

    async def _handler(self, ws: ServerConnection) -> None:
        self._clients.add(ws)
        logger.info("Frontend connected (%d clients)", len(self._clients))
        try:
            async for msg in ws:
                logger.debug("Frontend message: %s", msg)
                data = json.loads(msg)
                if data.get("type") == "touch":
                    area = data.get("area", "body")
                    self._last_touch = {
                        "area": area,
                        "x": data.get("x", 0),
                        "y": data.get("y", 0),
                        "time": time.time(),
                    }
                    logger.info("Touch: area=%s", area)
                    if self._touch_handler:
                        try:
                            await self._touch_handler(area)
                        except Exception as e:
                            logger.error("Touch handler error: %s", e)
                elif data.get("type") == "client_log":
                    level = data.get("level", "log")
                    message = data.get("message", "")
                    self._client_logs.append(f"[{level}] {message}")
                    if len(self._client_logs) > 500:
                        self._client_logs = self._client_logs[-300:]
                elif data.get("type") == "get_logs":
                    logs = self._client_logs[:]
                    self._client_logs.clear()
                    await ws.send(json.dumps({"type": "logs_response", "logs": logs[-50:]}))
                elif data.get("type") == "get_touch":
                    touch = self._last_touch
                    self._last_touch = None
                    await ws.send(json.dumps({"type": "touch_response", "touch": touch}))
                else:
                    await self._broadcast_others(ws, msg)
        except websockets.ConnectionClosed:
            pass
        finally:
            self._clients.discard(ws)
            logger.info("Frontend disconnected (%d clients)", len(self._clients))

    async def _broadcast_others(self, sender: ServerConnection, raw: str) -> None:
        others = [ws for ws in self._clients if ws is not sender]
        if not others:
            return
        await asyncio.gather(*[ws.send(raw) for ws in others], return_exceptions=True)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False)
        logger.debug("Broadcast: %s", raw)

        if self._client_mode:
            if self._client_ws:
                try:
                    await self._client_ws.send(raw)
                except Exception as e:
                    logger.error("Client send error: %s", e)
            else:
                logger.warning("PushServer client not connected")
            return

        if not self._clients:
            logger.debug("No connected frontends, skipping broadcast")
            return
        clients = list(self._clients)
        loop = self._loop
        if loop is None:
            logger.warning("PushServer loop not set, cannot broadcast")
            return
        current_loop = asyncio.get_running_loop()
        if current_loop is loop:
            coros = [ws.send(raw) for ws in clients]
            await asyncio.gather(*coros, return_exceptions=True)
        else:
            # Cross-loop: schedule in the PushServer's loop
            coros = [ws.send(raw) for ws in clients]
            futures = [asyncio.run_coroutine_threadsafe(c, loop) for c in coros]
            for f in futures:
                try:
                    f.result(timeout=5)
                except Exception:
                    pass

    # ── high-level API ──

    async def display_text(self, model_index: int, text: str, duration: int = 3000) -> None:
        await self.broadcast({
            "type": "display_text",
            "model": model_index,
            "text": text,
            "duration": duration,
        })

    async def set_expression(self, model_index: int, exp_id: int) -> None:
        await self.broadcast({
            "type": "set_expression",
            "model": model_index,
            "exp_id": exp_id,
        })

    async def clear_expression(self, model_index: int) -> None:
        await self.broadcast({
            "type": "clear_expression",
            "model": model_index,
        })

    async def trigger_motion(self, model_index: int, motion: str) -> None:
        await self.broadcast({
            "type": "trigger_motion",
            "model": model_index,
            "motion": motion,
        })

    async def set_position(self, model_index: int, x: int, y: int) -> None:
        await self.broadcast({
            "type": "set_position",
            "model": model_index,
            "x": x,
            "y": y,
        })

    async def set_effect(self, effect_id: int) -> None:
        await self.broadcast({
            "type": "set_effect",
            "effect_id": effect_id,
        })

    async def set_mouth_open(self, value: float) -> None:
        await self.broadcast({
            "type": "set_mouth_open",
            "value": value,
        })

    def pop_touch(self) -> dict[str, Any] | None:
        """Return and clear the last touch event."""
        t = self._last_touch
        self._last_touch = None
        return t

    def pop_client_logs(self) -> list[str]:
        """Return and clear client logs."""
        logs = self._client_logs[:]
        self._client_logs.clear()
        return logs

    async def request_logs(self) -> list[str]:
        """Request logs from the standalone PushServer (client mode)."""
        if not self._client_ws:
            return []
        try:
            await self._client_ws.send(json.dumps({"type": "get_logs"}))
            resp = await asyncio.wait_for(self._client_ws.recv(), timeout=5)
            data = json.loads(resp)
            return data.get("logs", [])
        except Exception as e:
            logger.error("Failed to request logs: %s", e)
            return []

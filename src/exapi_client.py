import asyncio
import json
import logging
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

logger = logging.getLogger(__name__)


class ExAPIClient:
    def __init__(self, url: str):
        self._url = url
        self._ws: ClientConnection | None = None
        self._msg_id = 0

    async def connect(self) -> None:
        if self._ws is not None:
            return
        self._ws = await websockets.connect(self._url)
        logger.info("Connected to ExAPI at %s", self._url)

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

    def _next_msg_id(self) -> int:
        self._msg_id += 1
        return self._msg_id

    async def send(self, msg: int, data: Any = None, wait_response: bool = False) -> dict | None:
        if self._ws is None:
            await self.connect()

        payload: dict[str, Any] = {
            "msg": msg,
            "msgId": self._next_msg_id(),
        }
        if data is not None:
            payload["data"] = data

        raw = json.dumps(payload, ensure_ascii=False)
        logger.debug("Send: %s", raw)
        assert self._ws is not None
        await self._ws.send(raw)

        if not wait_response:
            return None

        try:
            resp_raw = await asyncio.wait_for(self._ws.recv(), timeout=5)
            logger.debug("Recv: %s", resp_raw)
            return json.loads(resp_raw)
        except asyncio.TimeoutError:
            logger.debug("No response received")
            return None

    async def display_text(
        self,
        model_index: int,
        text: str,
        duration: int = 3000,
    ) -> dict | None:
        return await self.send(11000, {
            "id": model_index,
            "text": text,
            "duration": duration,
        })

    async def set_expression(self, model_index: int, exp_id: int) -> dict | None:
        return await self.send(13300, {
            "id": model_index,
            "expId": exp_id,
        })

    async def clear_expression(self, model_index: int) -> dict | None:
        return await self.send(13302, model_index)

    async def trigger_motion(self, model_index: int, motion: str) -> dict | None:
        return await self.send(13200, {
            "id": model_index,
            "type": 0,
            "mtn": motion,
        })

    async def set_position(self, model_index: int, x: int, y: int) -> dict | None:
        return await self.send(13400, {
            "id": model_index,
            "posX": x,
            "posY": y,
        })

    async def set_effect(self, effect_id: int) -> dict | None:
        return await self.send(14000, effect_id)

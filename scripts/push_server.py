#!/usr/bin/env python3
"""
独立的 PushServer 脚本：只运行 WebSocket 服务器，不运行 MCP Server。
用于测试和调试。
"""

import asyncio
import sys
sys.path.insert(0, '.')

from src.push_server import PushServer

push = PushServer('0.0.0.0', 10086)

async def main():
    await push.start()
    print('PushServer running on ws://0.0.0.0:10086', flush=True)
    await asyncio.Future()  # run forever

asyncio.run(main())

#!/usr/bin/env python3
"""
Agent 桥接脚本：调用 openclaw agent，将回复显示到 Live2D。
用法：python scripts/agent_bridge.py "你的消息"
"""

import asyncio
import json
import re
import subprocess
import sys
import websockets

PUSHSERVER_URL = "ws://127.0.0.1:10086"


def strip_ansi(text: str) -> str:
    """移除 ANSI 颜色代码"""
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


async def send_to_live2d(text: str, expression: str = "happy"):
    """发送文字和表情到 Live2D"""
    expressions = {
        "happy": 6, "sad": 5, "angry": 8, "surprised": 0,
        "love": 19, "shy": 6, "pout": 18, "squint": 9,
        "dead_fish": 9, "nn_eyes": 7, "dark_face": 4,
        "money_eyes": 11, "teary": 17, "cat_eyes": 0, "neutral": -1,
    }
    exp_id = expressions.get(expression, 6)
    
    async with websockets.connect(PUSHSERVER_URL) as ws:
        await ws.send(json.dumps({
            "type": "display_text",
            "model": 0,
            "text": text,
            "duration": 10000,
        }))
        if exp_id != -1:
            await ws.send(json.dumps({
                "type": "set_expression",
                "model": 0,
                "exp_id": exp_id,
            }))
        print(f"[Live2D] 显示: {text[:50]}... 表情: {expression}")


def call_agent(message: str) -> str:
    """调用 openclaw agent 获取回复"""
    cmd = [
        "openclaw", "agent",
        "-m", message,
        "--agent", "vivian",
        "--local",
        "--timeout", "60",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    # 过滤掉日志行，只保留回复
    lines = result.stdout.strip().split('\n')
    reply_lines = []
    for line in lines:
        # 移除 ANSI 颜色代码
        clean_line = strip_ansi(line)
        # 跳过日志行（以 [ 开头或空行）
        if clean_line.startswith('[') or not clean_line.strip():
            continue
        reply_lines.append(clean_line)
    return '\n'.join(reply_lines).strip()


async def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/agent_bridge.py \"你的消息\"")
        print("示例: python scripts/agent_bridge.py \"你好呀\"")
        sys.exit(1)
    
    message = sys.argv[1]
    print(f"你: {message}")
    
    # 调用 agent
    print("正在调用 agent...")
    reply = call_agent(message)
    print(f"Agent: {reply}")
    
    if reply:
        # 根据回复内容选择表情
        expression = "happy"
        if any(w in reply for w in ["哼", "才不是", "笨蛋"]):
            expression = "pout"
        elif any(w in reply for w in ["开心", "高兴", "嘻嘻"]):
            expression = "happy"
        elif any(w in reply for w in ["难过", "伤心", "抱歉"]):
            expression = "sad"
        elif any(w in reply for w in ["生气", "讨厌", "烦"]):
            expression = "angry"
        elif any(w in reply for w in ["惊讶", "诶", "啊"]):
            expression = "surprised"
        elif any(w in reply for w in ["喜欢", "爱", "感动"]):
            expression = "love"
        elif any(w in reply for w in ["害羞", "脸红"]):
            expression = "shy"
        elif any(w in reply for w in ["得意", "哼哼"]):
            expression = "squint"
        elif any(w in reply for w in ["无语", "服了"]):
            expression = "dead_fish"
        
        await send_to_live2d(reply, expression)


if __name__ == "__main__":
    asyncio.run(main())

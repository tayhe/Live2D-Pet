# Live2D AI Companion

通过 MCP 协议让 AI Agent（mimocode、openclaw、hermes）控制 Live2DViewerEX 桌面模型的表情、动作、语音和位置，作为 agent 的视觉化身。

## 架构

```
AI Agent (mimocode / openclaw / hermes)
    │  MCP 工具调用
    ↓
MCP Server (Python)
    │  WebSocket → ExAPI
    ↓
Live2DViewerEX
```

## 前置条件

- Python 3.10+
- [Live2DViewerEX](https://store.steampowered.com/app/616720/)（Steam 购买安装）
- 支持 MCP 的 AI Agent

## 安装

推荐使用 `uv` 创建虚拟环境并安装：

```bash
uv venv
uv pip install -e .
```

或使用传统方式：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## 配置

编辑 `config.yaml`，根据你的 Live2D 模型调整表情和动作映射。

### 当前默认配置

```yaml
exapi:
  host: 127.0.0.1
  port: 10086          # Live2DViewerEX ExAPI 默认端口

model:
  index: 0             # 模型槽位，0-based

expressions:           # 语义名称 → 模型 expId（已实测该模型可用）
  happy: 0
  sad: 1
  angry: 2
  surprised: 3
  neutral: -1          # -1 = 清除表情

motions:               # 语义名称 → motion group 名称（已实测该模型可用）
  tap: "Tap"
  idle: "Idle"
  tap_body: "TapBody"

effects:
  rain: 100100
  snow: 100110
```

### 如何确定你的模型有哪些可用的 expId 和 motion

`config.yaml` 中的表情 ID 和动作名称是 Live2D 模型自带的，不同模型不一样。可以通过以下步骤确定：

1. **测试表情 ID**（0~9 或更大）：
   ```bash
   .venv\Scripts\python.exe -c "
   import asyncio, json, websockets
   async def test():
       ws = await websockets.connect('ws://127.0.0.1:10086/api')
       for expId in range(10):
           await ws.send(json.dumps({'msg': 13300, 'msgId': expId+1, 'data': {'id': 0, 'expId': expId}}))
           print(f'expId={expId}')
           await asyncio.sleep(5)
       await ws.close()
   asyncio.run(test())
   "
   ```

2. **测试动作 group 名称**（每个停留 5-8 秒观察）：
   ```bash
   .venv\Scripts\python.exe -c "
   import asyncio, json, websockets
   async def test():
       ws = await websockets.connect('ws://127.0.0.1:10086/api')
       for mtn in ['Tap', 'Idle', 'TapBody', 'TapHead', 'Flick', 'Shake', 'nod', 'shake']:
           await ws.send(json.dumps({'msg': 13200, 'msgId': 1, 'data': {'id': 0, 'type': 0, 'mtn': mtn}}))
           print(mtn)
           await asyncio.sleep(6)
       await ws.close()
   asyncio.run(test())
   "
   ```

3. 找到有效的 ID/名称后，更新 `config.yaml` 的映射表。

## 使用

### 1. 启动 Live2DViewerEX 并启用 ExAPI

1. 启动 Live2DViewerEX，加载你的模型
2. 在 Live2DViewerEX 主程序设置中启用 ExAPI（默认端口 10086）
3. 验证 ExAPI 已监听：
   ```bash
   netstat -ano | findstr "10086"
   ```

### 2. 启动 MCP Server

```bash
.venv\Scripts\python.exe -m src.server
```

### 3. 在 Agent 中配置 MCP

将 MCP Server 注册到你的 agent 配置中：

```json
{
  "mcpServers": {
    "live2d": {
      "command": "F:\\Syncthing\\cloud\\Projects\\Live2D\\.venv\\Scripts\\python.exe",
      "args": ["-m", "src.server"],
      "cwd": "F:\\Syncthing\\cloud\\Projects\\Live2D"
    }
  }
}
```

> 注意：`command` 要使用 `.venv\Scripts\python.exe` 的绝对路径，否则可能使用错误的 Python 环境。

### 4. 调用工具

Agent 可以调用以下 MCP 工具：

| 工具 | 功能 | 参数 | ExAPI msg |
|------|------|------|-----------|
| `say` | 说话（显示文字气泡） | `text: str`, `duration?: int` (默认 3000ms) | 11000 |
| `set_expression` | 设置表情 | `expression: str` (语义名称) | 13300 |
| `play_motion` | 播放动作 | `motion: str` (语义名称) | 13200 |
| `set_position` | 移动位置 | `x: int`, `y: int` | 13400 |
| `set_effect` | 设置特效 | `effect: str` (语义名称) | 14000 |

使用示例（agent 视角）：

```
say("你好呀！")
set_expression("happy")
play_motion("tap")
set_position(500, 300)
set_effect("rain")
```

## 项目结构

```
live2d-ai-companion/
├── src/
│   ├── __init__.py
│   ├── server.py           # MCP Server 入口，定义 5 个工具
│   ├── exapi_client.py     # ExAPI WebSocket 客户端封装
│   └── config.py           # 配置加载与验证
├── config.yaml             # 模型表情/动作映射配置
├── pyproject.toml          # Python 项目依赖
├── .venv/                  # Python 虚拟环境
├── .gitignore
└── README.md
```

## 核心实现细节

### ExAPI 客户端 (`src/exapi_client.py`)

- 连接：`ws://127.0.0.1:10086/api`
- 消息格式：`{"msg": <int>, "msgId": <int>, "data": <object>}`
- **不等待响应**：Live2DViewerEX 对大多数消息不回响应，所以 `send()` 默认不阻塞等待
- 自动维护 `msgId` 单调递增

### MCP 工具语义层 (`src/server.py`)

Agent 看到的是语义化名称（`happy`、`tap`），通过 `config.yaml` 映射到模型的原始 ID（`expId: 0`、`mtn: "Tap"`）。换模型只需改配置，agent 调用方式不变。

## 后续计划

- [ ] TTS 语音合成（Edge TTS）
- [ ] 口型同步
- [ ] 模型交互事件监听（10000/10002）
- [ ] 多模型支持
- [ ] 热更新配置（无需重启）

## 参考

- [Live2DViewerEX ExAPI 文档](https://live2d.pavostudio.com/doc/en-us/exapi/)
- [ExAPI GitHub 仓库](https://github.com/pavostudio/ExAPI)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
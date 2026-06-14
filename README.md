# Live2D AI Companion

通过 MCP 协议让 AI Agent（mimocode、openclaw、hermes）控制 Live2D 桌面模型的表情、动作、文字气泡、位置和特效，作为 agent 的视觉化身。

## 架构

```
AI Agent (mimocode / openclaw / hermes)
    │  MCP 工具调用（stdio）
    ↓
MCP Server (Python)
    │  PushServer WebSocket 广播
    ↓
React Frontend (pixi-live2d-display)
    │  渲染 Live2D 模型
    ↓
浏览器窗口
```

## 前置条件

- Python 3.10+
- Node.js 18+
- 支持 MCP 的 AI Agent（如 mimocode）

## 安装

### 后端（Python）

```bash
uv venv
uv pip install -e .
```

### 前端（React）

```bash
cd frontend
npm install
```

## 配置

编辑 `config.yaml`，根据你的 Live2D 模型调整表情和动作映射。

### 当前默认配置（PinkFox 模型）

```yaml
exapi:
  host: 127.0.0.1
  port: 10086          # PushServer WebSocket 端口

model:
  index: 0             # 模型槽位，0-based

expressions:           # 语义名称 → exp_id（对应 frontend Live2DModel.jsx 的 EXPRESSIONS 字典）
  happy: 3             # 红脸
  sad: 5               # 眼泪
  angry: 7             # 生气瘪嘴
  surprised: 0         # 猫猫眼
  love: 19             # 爱心
  shy: 3               # 红脸（同 happy）
  pout: 11             # 嘟嘴
  squint: 9            # 咪咪眼
  dead_fish: 8         # 死鱼眼
  nn_eyes: 6           # nn眼
  dark_face: 4         # 黑脸
  money_eyes: 18       # 钱钱眼
  teary: 17            # 泪眼
  cat_eyes: 0          # 猫猫眼
  ears_off: 12         # 兽耳消失
  tail_off: 13         # 尾巴消失
  neutral: -1          # 清除表情

motions:               # 语义名称 → motion group 名称
  idle: ""
  tap_body: ""

effects:
  rain: 100100
  snow: 100110
```

### 换模型

1. 将模型文件放入 `frontend/public/models/<模型名>/`
2. 修改 `frontend/src/components/Live2DModel.jsx` 中的 `MODEL_PATH` 和 `EXPRESSIONS` 字典
3. 更新 `config.yaml` 的 `expressions` 映射
4. 重启 MCP Server 和前端

## 使用

### 1. 启动 MCP Server

```bash
.venv\Scripts\python.exe -m src.server
```

MCP Server 启动时会自动在 `ws://127.0.0.1:10086` 启动 PushServer WebSocket 服务。

### 2. 启动前端

```bash
cd frontend
npm run dev
```

前端会在 `http://localhost:5173` 启动，自动连接 PushServer。

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

| 工具 | 功能 | 参数 |
|------|------|------|
| `say` | 说话（显示文字气泡） | `text: str`, `duration?: int` (默认 3000ms) |
| `set_expression` | 设置表情 | `expression: str` (语义名称) |
| `say_and_express` | **说话+表情（推荐）** | `text: str`, `expression?: str` (默认 "happy"), `duration?: int` |
| `play_motion` | 播放动作 | `motion: str` (语义名称) |
| `set_position` | 移动位置 | `x: int`, `y: int` |
| `set_effect` | 设置特效 | `effect: str` (语义名称) |

使用示例（agent 视角）：

```
# 最常用：说话+表情
say_and_express("你好呀~", "happy")
say_and_express("哼，才不是担心你呢...", "pout")

# 单独控制
set_expression("surprised")
play_motion("tap_body")
set_position(500, 300)
set_effect("rain")
```

## 项目结构

```
live2d-ai-companion/
├── src/
│   ├── __init__.py
│   ├── server.py           # MCP Server 入口，定义 6 个工具
│   ├── push_server.py      # WebSocket 服务器，向前端推送命令
│   └── config.py           # 配置加载与验证
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Live2DModel.jsx    # Live2D 渲染核心（pixi-live2d-display）
│   │   │   └── DialogueBox.jsx    # 文字气泡组件
│   │   ├── api/
│   │   │   └── ws.js              # WebSocket 客户端，接收 PushServer 命令
│   │   ├── App.jsx                # 主应用，连接 WebSocket 和组件
│   │   └── App.css                # 样式
│   ├── public/
│   │   ├── libs/
│   │   │   └── live2dcubismcore.min.js  # Cubism SDK Core
│   │   └── models/                # Live2D 模型文件
│   │       ├── PinkFox/           # 当前默认模型
│   │       ├── Hiyori/            # 备选模型
│   │       └── Haru/              # 备选模型
│   └── package.json
├── config.yaml             # 模型表情/动作映射配置
├── pyproject.toml          # Python 项目依赖
└── README.md
```

## 核心实现细节

### PushServer (`src/push_server.py`)

- WebSocket 服务器，监听 `ws://127.0.0.1:10086`
- 接收 MCP 工具调用，广播命令到所有连接的前端
- 支持客户端间消息转发（用于调试）

### 前端渲染 (`frontend/src/components/Live2DModel.jsx`)

- 使用 `pixi-live2d-display` 加载 Cubism 3/4 模型
- 通过 `setParameterValueById` 控制表情参数（每帧写入，防止 idle motion 覆盖）
- PinkFox 嘴型是 3 参数复合：`ParamMouthOpenY` + `Tonguelicking` + `MouthBig2`(×0.6)
- 表情 8 秒后自动清除

### WebSocket 协议

前端连接 `ws://localhost:10086`，接收 JSON 命令：

```json
{"type": "display_text", "model": 0, "text": "你好", "duration": 3000}
{"type": "set_expression", "model": 0, "exp_id": 3}
{"type": "clear_expression", "model": 0}
{"type": "trigger_motion", "model": 0, "motion": ""}
{"type": "set_position", "model": 0, "x": 100, "y": 200}
{"type": "set_effect", "effect_id": 100100}
{"type": "set_mouth_open", "value": 1.0}
```

## PinkFox 表情参数速查

| 语义名 | exp_id | 参数 ID | 视觉效果 |
|--------|--------|---------|----------|
| happy/shy | 3 | key2 | 红脸 |
| dark_face | 4 | key3 | 黑脸 |
| sad | 5 | key4 | 眼泪 |
| nn_eyes | 6 | key5 | nn眼 |
| angry | 7 | key6 | 生气瘪嘴 |
| dead_fish | 8 | key7 | 死鱼眼 |
| squint | 9 | key8 | 咪咪眼 |
| cat_eyes/surprised | 0 | key9 | 猫猫眼 |
| pout | 11 | key12 | 嘟嘴 |
| love | 19 | key16 | 爱心 |
| teary | 17 | key17 | 泪眼 |
| money_eyes | 18 | key11 | 钱钱眼 |
| ears_off | 12 | key19 | 兽耳消失 |
| tail_off | 13 | key20 | 尾巴消失 |
| neutral | -1 | — | 清除表情 |

## 后续计划

- [ ] TTS 语音合成 → 嘴型自动同步（wlipsync）
- [ ] Agent 根据情感自动选择表情
- [ ] 点击交互（触摸模型不同区域触发不同反应）
- [ ] 桌面悬浮窗模式（Electron/Tauri）
- [ ] 多模型切换
- [ ] 热更新配置（无需重启）

## 参考

- [pixi-live2d-display 文档](https://guansss.github.io/pixi-live2d-display/)
- [Live2D Cubism SDK](https://www.live2d.com/en/sdk/download/native/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [nana 项目](https://github.com/艾拉)（参考实现）

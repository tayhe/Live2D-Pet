import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from src.config import load_config
from src.exapi_client import ExAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = load_config(Path(__file__).parent.parent / "config.yaml")
exapi = ExAPIClient(config.exapi.url)

mcp = FastMCP(
    "live2d-companion",
    instructions=(
        "Live2D 桌面伴侣控制工具。"
        "使用 say 让角色说话，set_expression 控制表情，"
        "play_motion 播放动作，set_position 移动位置，"
        "set_effect 添加天气特效。"
    ),
)


@mcp.tool()
async def say(text: str, duration: int = 3000) -> str:
    """让 Live2D 角色说话，显示文字气泡。

    Args:
        text: 要显示的文字内容
        duration: 气泡显示时长（毫秒），默认 3000
    """
    await exapi.display_text(config.model.index, text, duration)
    return f"已显示文字：{text}"


@mcp.tool()
async def set_expression(expression: str) -> str:
    """设置 Live2D 角色的表情。

    Args:
        expression: 表情名称，如 happy, sad, angry, surprised, neutral
    """
    if expression not in config.expressions:
        available = ", ".join(config.expressions.keys())
        return f"未知表情 '{expression}'。可用：{available}"

    exp_id = config.expressions[expression]
    if exp_id == -1:
        await exapi.clear_expression(config.model.index)
        return "已清除表情"
    else:
        await exapi.set_expression(config.model.index, exp_id)
        return f"已设置表情：{expression}"


@mcp.tool()
async def play_motion(motion: str) -> str:
    """播放 Live2D 角色的动作。

    Args:
        motion: 动作名称，如 idle, wave, nod
    """
    if motion not in config.motions:
        available = ", ".join(config.motions.keys())
        return f"未知动作 '{motion}'。可用：{available}"

    mtn = config.motions[motion]
    await exapi.trigger_motion(config.model.index, mtn)
    return f"已播放动作：{motion}"


@mcp.tool()
async def set_position(x: int, y: int) -> str:
    """移动 Live2D 角色在屏幕上的位置。

    Args:
        x: 水平像素坐标（原点在左下角）
        y: 垂直像素坐标（原点在左下角）
    """
    await exapi.set_position(config.model.index, x, y)
    return f"已移动到 ({x}, {y})"


@mcp.tool()
async def set_effect(effect: str) -> str:
    """设置 Live2D 场景特效。

    Args:
        effect: 特效名称，如 rain, snow
    """
    if effect not in config.effects:
        available = ", ".join(config.effects.keys())
        return f"未知特效 '{effect}'。可用：{available}"

    effect_id = config.effects[effect]
    await exapi.set_effect(effect_id)
    return f"已设置特效：{effect}"


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

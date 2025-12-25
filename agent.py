#!/usr/bin/env python3
"""
Claude Agent Framework - 主入口

多智能体研究系统入口点，提供交互式命令行界面。
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def setup_import_path() -> None:
    """设置导入路径"""
    # 添加框架目录到路径
    framework_dir = Path(__file__).parent.parent
    if str(framework_dir) not in sys.path:
        sys.path.insert(0, str(framework_dir))


setup_import_path()

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

from claude_agent_framework.config import (
    FrameworkConfig,
    validate_api_key,
)
from claude_agent_framework.utils import (
    SubagentTracker,
    TranscriptWriter,
    process_message,
    setup_session,
)


async def run_research_session(
    config: FrameworkConfig | None = None,
    single_query: str | None = None,
) -> None:
    """
    运行研究会话

    Args:
        config: 框架配置，None 则使用默认配置
        single_query: 单次查询模式，执行后退出
    """
    # 使用默认配置
    if config is None:
        config = FrameworkConfig()

    # 验证 API Key
    if not validate_api_key():
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set it before running:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        return

    # 确保目录存在
    config.ensure_directories()

    # 设置会话
    session_dir, transcript_path, tool_log_path = setup_session(config.logs_dir)
    print(f"Session logs: {session_dir}")

    # 初始化工具
    transcript = TranscriptWriter(transcript_path)
    tracker = SubagentTracker(tool_log_path, transcript)

    # 配置 Hooks
    hooks = {
        "PreToolUse": [
            HookMatcher(
                matcher=None,  # 匹配所有工具
                hooks=[tracker.pre_tool_use_hook],
            )
        ],
        "PostToolUse": [
            HookMatcher(
                matcher=None,
                hooks=[tracker.post_tool_use_hook],
            )
        ],
    }

    # 加载智能体配置
    try:
        lead_prompt = config.load_lead_agent_prompt()
        agents = config.to_agents_dict()
    except FileNotFoundError as e:
        print(f"Error loading prompts: {e}")
        return

    try:
        # 单次查询模式
        if single_query:
            await _execute_query(
                query=single_query,
                lead_prompt=lead_prompt,
                agents=agents,
                hooks=hooks,
                config=config,
                tracker=tracker,
                transcript=transcript,
            )
        else:
            # 交互模式
            await _interactive_loop(
                lead_prompt=lead_prompt,
                agents=agents,
                hooks=hooks,
                config=config,
                tracker=tracker,
                transcript=transcript,
            )

    except KeyboardInterrupt:
        print("\n\nSession interrupted by user.")

    finally:
        # 清理资源
        transcript.close()
        tracker.close()
        print(f"\nSession saved to: {session_dir}")


async def _execute_query(
    query: str,
    lead_prompt: str,
    agents: dict,
    hooks: dict,
    config: FrameworkConfig,
    tracker: SubagentTracker,
    transcript: TranscriptWriter,
) -> None:
    """执行单次查询"""
    transcript.user_input(query)

    # 配置 SDK 选项
    options = ClaudeAgentOptions(
        permission_mode=config.permission_mode,
        setting_sources=config.setting_sources,
        system_prompt=lead_prompt,
        allowed_tools=config.lead_agent_tools,
        agents=agents,
        hooks=hooks,
        model=config.lead_agent_model,
    )

    # 执行查询
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt=query)

        async for msg in client.receive_response():
            process_message(msg, tracker, transcript)


async def _interactive_loop(
    lead_prompt: str,
    agents: dict,
    hooks: dict,
    config: FrameworkConfig,
    tracker: SubagentTracker,
    transcript: TranscriptWriter,
) -> None:
    """交互式循环"""
    print("\n" + "=" * 50)
    print("Claude Agent Framework - 研究智能体系统")
    print("=" * 50)
    print("\n输入研究主题开始，输入 'quit' 或 'exit' 退出。")
    print("提示：可以使用 /research <主题> 启动研究任务")

    while True:
        try:
            # 获取用户输入
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            # 执行查询
            await _execute_query(
                query=user_input,
                lead_prompt=lead_prompt,
                agents=agents,
                hooks=hooks,
                config=config,
                tracker=tracker,
                transcript=transcript,
            )

        except EOFError:
            print("\nGoodbye!")
            break


def main() -> None:
    """命令行入口点"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Agent Framework - Multi-Agent Research System"
    )
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="Single query mode: execute query and exit",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="haiku",
        choices=["haiku", "sonnet", "opus"],
        help="Model to use for lead agent (default: haiku)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 创建配置
    config = FrameworkConfig(lead_agent_model=args.model)

    # 运行会话
    asyncio.run(run_research_session(config=config, single_query=args.query))


if __name__ == "__main__":
    main()

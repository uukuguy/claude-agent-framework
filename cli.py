#!/usr/bin/env python3
"""
Unified CLI for Claude Agent Framework.

Provides a single entry point for all architectures.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def setup_import_path() -> None:
    """Setup import path."""
    framework_dir = Path(__file__).parent.parent
    if str(framework_dir) not in sys.path:
        sys.path.insert(0, str(framework_dir))


setup_import_path()

from claude_agent_framework.config import validate_api_key
from claude_agent_framework.core.registry import (
    get_architecture,
    get_architecture_info,
    list_architectures,
)
from claude_agent_framework.core.session import AgentSession

# Import architectures to trigger registration
import claude_agent_framework.architectures  # noqa: F401


def print_architectures() -> None:
    """Print available architectures."""
    print("\nAvailable Architectures:")
    print("=" * 50)

    for name, info in get_architecture_info().items():
        print(f"\n  {name}")
        print(f"    {info['description']}")

    print()


async def run_architecture(
    arch_name: str,
    query: str | None = None,
    model: str = "haiku",
    interactive: bool = False,
    verbose: bool = False,
) -> None:
    """
    Run the specified architecture.

    Args:
        arch_name: Name of the architecture
        query: Single query (None for interactive mode)
        model: Model to use
        interactive: Force interactive mode
        verbose: Enable verbose logging
    """
    # Validate API key
    if not validate_api_key():
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set it before running:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        return

    # Get architecture class
    try:
        arch_class = get_architecture(arch_name)
    except KeyError as e:
        print(f"Error: {e}")
        print_architectures()
        return

    # Create architecture instance
    arch = arch_class()
    session = AgentSession(arch)

    try:
        if query and not interactive:
            # Single query mode
            await _execute_query(session, query)
        else:
            # Interactive mode
            await _interactive_loop(session, arch_name)

    except KeyboardInterrupt:
        print("\n\nSession interrupted by user.")

    finally:
        await session.teardown()
        if session.session_dir:
            print(f"\nSession saved to: {session.session_dir}")


async def _execute_query(session: AgentSession, query: str) -> None:
    """Execute a single query."""
    print(f"\nExecuting with {session.architecture.name} architecture...")
    print("-" * 50)

    async for msg in session.run(query):
        # Message processing is handled by session
        pass

    print("-" * 50)
    print("Done.")


async def _interactive_loop(session: AgentSession, arch_name: str) -> None:
    """Run interactive loop."""
    print("\n" + "=" * 50)
    print(f"Claude Agent Framework - {arch_name} Architecture")
    print("=" * 50)
    print(f"\nUsing: {session.architecture.description}")
    print("\nType your query or 'quit' to exit.")

    while True:
        try:
            user_input = input("\n> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            await _execute_query(session, user_input)

        except EOFError:
            print("\nGoodbye!")
            break


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Agent Framework - Multi-Architecture Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available architectures
  python -m claude_agent_framework.cli --list

  # Run research architecture with query
  python -m claude_agent_framework.cli --arch research -q "研究AI市场趋势"

  # Run pipeline architecture interactively
  python -m claude_agent_framework.cli --arch pipeline -i

  # Run debate architecture
  python -m claude_agent_framework.cli --arch debate -q "是否应该使用微服务架构"
""",
    )

    parser.add_argument(
        "--arch",
        "-a",
        type=str,
        default="research",
        help="Architecture to use (default: research)",
    )
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="Single query mode: execute query and exit",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Force interactive mode",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="haiku",
        choices=["haiku", "sonnet", "opus"],
        help="Model to use (default: haiku)",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available architectures",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # List architectures
    if args.list:
        print_architectures()
        return

    # Run architecture
    asyncio.run(
        run_architecture(
            arch_name=args.arch,
            query=args.query,
            model=args.model,
            interactive=args.interactive,
            verbose=args.verbose,
        )
    )


if __name__ == "__main__":
    main()

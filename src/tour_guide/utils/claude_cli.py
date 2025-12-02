"""Claude CLI wrapper for making LLM calls."""

import subprocess
from tour_guide.logging import get_logger

logger = get_logger("utils.claude_cli")


class ClaudeError(Exception):
    """Claude CLI error."""

    pass


def call_claude(prompt: str, timeout: int = 30, model: str = None) -> str:
    """
    Call Claude CLI with a prompt.

    Args:
        prompt: The prompt to send to Claude
        timeout: Timeout in seconds (default: 30)
        model: Model to use (default: from config)

    Returns:
        Claude's response as a string

    Raises:
        ClaudeError: If Claude CLI fails or times out
    """
    # Build command
    cmd = ["claude"]

    if model:
        cmd.extend(["--model", model])

    # Add prompt
    cmd.extend(["-p", prompt])

    logger.debug(f"Calling Claude CLI with prompt length: {len(prompt)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )

        response = result.stdout.strip()
        logger.debug(f"Claude response length: {len(response)}")
        return response

    except subprocess.TimeoutExpired:
        logger.error(f"Claude CLI timed out after {timeout}s")
        raise ClaudeError(f"Claude CLI timed out after {timeout}s")

    except subprocess.CalledProcessError as e:
        logger.error(f"Claude CLI failed: {e.stderr}")
        raise ClaudeError(f"Claude CLI failed: {e.stderr}")

    except FileNotFoundError:
        logger.error("Claude CLI not found")
        raise ClaudeError(
            "Claude CLI not found. Install with: pip install anthropic-cli"
        )

    except Exception as e:
        logger.error(f"Unexpected error calling Claude: {e}")
        raise ClaudeError(f"Unexpected error: {e}")

"""Simple agent functions for the extraction_agent service.

This module exports a small API the post route can call so we can
demonstrate that the agent's function runs when a POST is received.
"""

from typing import Optional


def process_text(text: Optional[str]) -> None:
    """Process the received text.

    For now just print to the container logs to indicate the function ran.

    Args:
        text: the text to process (may be None)
    """
    if text is None:
        print("agent.process_text called with no text")
    else:
        print("agent.process_text called with:", text)


def simple_notify() -> None:
    """Simple helper to show agent is reachable."""
    print("agent.simple_notify called")

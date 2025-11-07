"""Simple agent functions for the extraction_agent service.

This module exports a small API the post route can call so we can
demonstrate that the agent's function runs when a POST is received.
"""

from typing import Optional


def process_text(text: Optional[str]) -> Optional[str]:
    """Process the received text and return the processed text.

    Current implementation is a pass-through (returns the input). Update
    this function later to perform real extraction/normalization if needed.

    Args:
        text: the text to process (may be None)

    Returns:
        The processed text, or None if no processing was possible.
    """
    if text is None:
        print("agent.process_text called with no text")
        return None

    # Example processing: here we simply log and return the same text.
    print("agent.process_text called with:", text)
    # TODO: replace with real processing
    processed = text
    return processed


def simple_notify() -> None:
    """Simple helper to show agent is reachable."""
    print("agent.simple_notify called")

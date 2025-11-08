"""
memory_builder.py: Constructs memory text from a single stored summary.
"""

from typing import Optional, Dict, Any


def build_memory_prompt(summary_data: Optional[Dict[str, Any]]) -> str:
    """
    Build the memory prompt from summary data.

    Args:
        summary_data: Dictionary containing:
            - db_summary: The condensed summary
            - emergency: boolean
            - medically_relevant: boolean

    Returns:
        Formatted memory string for the prompt
    """
    if not summary_data:
        return ""

    db_summary = summary_data.get("db_summary", "").strip()
    if not db_summary or db_summary == "N/A":
        return ""

    # Add emergency/medical flags if present
    if summary_data.get("emergency"):
        return f"[EMERGENCY] {db_summary}"
    elif summary_data.get("medically_relevant"):
        return f"[MEDICAL] {db_summary}"
    else:
        return db_summary

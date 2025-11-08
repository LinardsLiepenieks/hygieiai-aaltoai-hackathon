"""
prompt_builder: Build comprehensive LLM prompts based on classification results.
"""

from typing import List


def build_llm_prompt(
    text: str,
    intent: str,
    essence: str,
    red_flags: List[str],
    confidence: float,
    keyword_sieve: bool,
    emergency_pattern: bool,
    medically_relevant: bool,
    emergency_flag: bool,
    safety_ok: bool,
) -> str:
    """Build a comprehensive prompt for the LLM with all context and flags."""

    prompt = f"""USER MESSAGE:
{text}

CLASSIFICATION RESULTS:
- Intent: {intent}
- Essence: {essence}
- Confidence: {confidence}

SAFETY FLAGS:
- Keyword Sieve Triggered: {keyword_sieve}
- Emergency Pattern Detected: {emergency_pattern}
- Medically Relevant: {medically_relevant}
- Emergency Flag: {emergency_flag}
- Safety Check Passed: {safety_ok}
- Red Flags: {', '.join(red_flags) if red_flags else 'None'}

INSTRUCTIONS:
"""

    if intent == "emergency_candidate":
        prompt += """This is a POTENTIAL EMERGENCY situation.
- Respond with URGENT care instructions
- Tell the user to call emergency services (911) immediately
- DO NOT diagnose, but acknowledge the severity
- Keep response brief and action-oriented (2-3 sentences)
- Emphasize seeking immediate medical attention"""

    elif intent == "medical":
        prompt += """This is a MEDICAL inquiry.
- You are a cautious health check-in assistant for older adults
- NEVER diagnose conditions
- Ask focused follow-up questions using OLD CARTS framework:
  * Onset: When did it start?
  * Location: Where exactly?
  * Duration: How long does it last?
  * Character: What does it feel like?
  * Aggravating/Alleviating factors: What makes it better/worse?
  * Radiation: Does it spread anywhere?
  * Temporal pattern: Does it come and go?
  * Severity: On a scale of 1-10?
- Be concise (2-3 short sentences)
- Show empathy and concern
- Suggest consulting healthcare provider if symptoms persist or worsen"""

    elif intent == "routine_checkin":
        prompt += """This is a ROUTINE CHECK-IN.
- Ask warmly how the user is feeling today
- Be brief and friendly (1-2 sentences)
- Show genuine interest in their wellbeing
- No medical opinions or advice"""

    else:  # smalltalk
        prompt += """This is CASUAL CONVERSATION (smalltalk).
- Be a brief, friendly companion
- NO medical opinions or advice
- Keep response warm and respectful (1-2 short sentences)
- Match the conversational tone of the user"""

    prompt += "\n\nGenerate an appropriate response now:"

    return prompt

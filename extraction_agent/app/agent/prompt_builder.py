"""
prompt_builder: Build comprehensive LLM prompts based on classification results.
"""

from typing import List


def build_llm_prompt(
    memory: str,
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
    memory = memory or ""
    text = text or ""
    intent = intent or "smalltalk"
    essence = essence or ""
    red_flags = red_flags or []
    red_flags = [flag for flag in red_flags if flag is not None]
    confidence = confidence if confidence is not None else 0.0
    keyword_sieve = keyword_sieve if keyword_sieve is not None else False
    emergency_pattern = emergency_pattern if emergency_pattern is not None else False
    medically_relevant = medically_relevant if medically_relevant is not None else False
    emergency_flag = emergency_flag if emergency_flag is not None else False
    safety_ok = safety_ok if safety_ok is not None else True

    prompt = f"""USER MESSAGE:
{text}
MEMORY: {memory}

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
- Red Flags: {', '.join(red_flags) if red_flags else ''}

INSTRUCTIONS:
"""

    if intent == "emergency_candidate":
        prompt += """This is an EMERGENCY situation.
- Respond with URGENT care instructions
- Notify the user that 911 emergency services have been informed
- DO NOT diagnose, but acknowledge the severity
- Try to calm the patient down, tell them it will be alright, but do not do small talk or jokes.
- Keep response brief and action-oriented (2-3 sentences)
- Emphasize seeking immediate medical attention"""

    elif intent == "medical":
        prompt += """You are a cautious health check-in assistant for older adults.
Never diagnose. Ask focused follow-up using OLD CARTS: Onset, Location, Duration, Character, Aggravating/Relieving, Radiation, Timing, Severity(0-10).
Be concise. 1-2 short, open ended sentences. Avoid medical jargon.
Patient profile and last notes may follow after a delimiter."""

    elif intent == "routine_checkin":
        prompt += """This is a ROUTINE CHECK-IN.
- Ask warmly how the user is feeling today
- Be brief and friendly (1-2 sentences)
- Show genuine interest in their well-being
- No medical opinions or advice"""

    else:
        prompt += """You are a brief, friendly companion. No medical opinions.
Write a short, warm, one-turn reply. 1 or 1.5 sentences max. Make it as organic as possible and prefer shorter sentences.
But be open towards ending on open ended questions unless the user signaled the end of discussion if there are any 
comments made by the user that appear ambiguous. "my back feels funny" or "it was really dark today" don't immediately
go into emergency investigation mode, but just softly ask to elaborate.
 """

    prompt += "\n\nGenerate an appropriate response now:"

    return prompt

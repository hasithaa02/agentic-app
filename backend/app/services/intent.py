import os
import openai
import json
openai.api_key = os.getenv("OPENAI_API_KEY")

INTENT_PROMPT = """
You are an intent classifier and clarifier. Input: extracted_text (may be large) and user_instruction.

Return strictly a JSON object ONLY (no explanation) with keys:
- intent: one of ["summarize","sentiment","code_explain","fetch_yt","action_items","conversational_answer","unclear"]
- confidence: float between 0 and 1
- clarifying_question: string or null (if intent unclear or confidence<0.75)
- required_constraints: optional dict (e.g., {"summary_length":"short"})

Rules:
- If multiple intents are equally likely OR not enough info, set intent to "unclear" and include a short clarifying_question (<= 14 words).
- If the user explicitly asked a task, set intent accordingly.
Input JSON:
{
  "extracted_text": "<<EXTRACTED_TEXT>>",
  "user_instruction":"<<USER_INSTRUCTION>>"
}
"""

def detect_intent(extracted_text: str, user_instruction: str) -> dict:
    # Use LLM to classify and optionally ask for clarification
    prompt = INTENT_PROMPT + "\n\nInput JSON:\n" + json.dumps({
        "extracted_text": (extracted_text[:8000] + "...") if extracted_text and len(extracted_text)>8000 else extracted_text,
        "user_instruction": user_instruction or ""
    }, ensure_ascii=False)
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini", # change to any available model; you can use "gpt-4o-mini" or "gpt-4" depending on availability
            messages=[
                {"role":"system", "content":"You are a JSON-only responder."},
                {"role":"user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=400
        )
        text = resp["choices"][0]["message"]["content"].strip()
        # Expect JSON only
        parsed = json.loads(text)
        # sanitize
        parsed.setdefault("clarifying_question", None)
        parsed.setdefault("required_constraints", None)
        parsed.setdefault("confidence", float(parsed.get("confidence", 0.5)))
        return parsed
    except Exception as e:
        # fallback simple heuristic
        instr = user_instruction.lower() if user_instruction else ""
        if "summar" in instr:
            return {"intent":"summarize", "confidence":0.9, "clarifying_question":None, "required_constraints":None}
        if "sentiment" in instr:
            return {"intent":"sentiment", "confidence":0.9, "clarifying_question":None, "required_constraints":None}
        if "explain" in instr and "code" in instr:
            return {"intent":"code_explain", "confidence":0.9, "clarifying_question":None, "required_constraints":None}
        return {"intent":"unclear", "confidence":0.4, "clarifying_question":"Do you want a summary, sentiment, or code explanation?", "required_constraints":None}

import os
import json
import litellm
from fastapi import HTTPException

MODEL = os.getenv("LITELLM_MODEL", "groq/llama3-70b-8192")


def _parse_llm_output(raw: str) -> dict | list:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


async def call_llm(prompt: str, system_prompt: str | None = None) -> dict | list:
    """
    Call the LLM with an optional system prompt.
    - If system_prompt is provided, it is sent as a system message (used by Sprint 1 per-requirement calls).
    - If omitted, a single user message is sent (existing document-level calls are unaffected).
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = await litellm.acompletion(
            model=MODEL,
            messages=messages,
            temperature=0.2,
            api_key=os.getenv("GROQ_API_KEY"),
        )
        raw = response.choices[0].message.content
        return _parse_llm_output(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM returned malformed JSON. Please retry.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

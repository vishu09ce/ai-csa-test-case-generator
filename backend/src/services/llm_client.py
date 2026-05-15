import os
import json
import asyncio
import litellm
from fastapi import HTTPException

MODEL = os.getenv("LITELLM_MODEL", "groq/llama3-70b-8192")

MAX_RETRIES = 3
BACKOFF_DELAYS = [1, 2, 4]  # seconds


def _parse_llm_output(raw: str) -> dict | list:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


async def call_llm(prompt: str, system_prompt: str | None = None) -> dict | list:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    last_error = None
    for attempt, delay in enumerate(BACKOFF_DELAYS):
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
            last_error = e
            is_rate_limit = "429" in str(e) or "rate_limit" in str(e).lower()
            if not is_rate_limit or attempt == len(BACKOFF_DELAYS) - 1:
                raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")
            await asyncio.sleep(delay)

    raise HTTPException(status_code=500, detail=f"LLM call failed after retries: {str(last_error)}")

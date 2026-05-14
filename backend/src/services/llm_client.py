import os
import json
import litellm
from fastapi import HTTPException

MODEL = os.getenv("LITELLM_MODEL", "groq/llama3-70b-8192")


async def call_llm(prompt: str) -> dict:
    try:
        response = await litellm.acompletion(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            api_key=os.getenv("GROQ_API_KEY"),
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM returned malformed JSON. Please retry.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

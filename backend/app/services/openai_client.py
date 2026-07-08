import json
from dataclasses import dataclass

from fastapi import HTTPException, status
from openai import OpenAI
from sqlmodel import Session

from app.config import get_settings
from app.models.usage import UsageEvent

# USD per 1M tokens (approximate; gpt-4o-mini pricing)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
}


@dataclass
class OpenAIResult:
    content: dict
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    input_rate, output_rate = MODEL_PRICING.get(model, (0.15, 0.60))
    return (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000


def get_openai_client() -> OpenAI:
    settings = get_settings()
    api_key = settings.openai_api_key.strip()
    if not api_key or api_key.startswith("sk-your"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key is not configured. Set OPENAI_API_KEY in backend/.env",
        )
    return OpenAI(api_key=api_key)


def chat_json(
    session: Session,
    *,
    company_id: int,
    operation: str,
    system_prompt: str,
    user_prompt: str,
) -> OpenAIResult:
    settings = get_settings()
    client = get_openai_client()
    model = settings.openai_model

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )

    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    total_tokens = usage.total_tokens if usage else prompt_tokens + completion_tokens
    cost = estimate_cost(model, prompt_tokens, completion_tokens)

    session.add(
        UsageEvent(
            company_id=company_id,
            operation=operation,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
        )
    )

    raw = response.choices[0].message.content or "{}"
    try:
        content = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI returned invalid JSON",
        ) from exc

    return OpenAIResult(
        content=content,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=cost,
    )

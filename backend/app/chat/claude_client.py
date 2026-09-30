"""Manual tool-use loop against the Anthropic Messages API.

A manual loop (rather than the beta tool_runner) keeps this hackathon build
free of a beta SDK dependency and gives full, auditable control over exactly
where customer_id gets injected into a tool call — never from the model.
"""
import json

import anthropic

from app.chat.tools import TOOL_DISPATCH, TOOLS
from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

MAX_TOOL_ITERATIONS = 5

SYSTEM_PROMPT = (
    "Je bent de 'Wat als?' financiële assistent van een Belgische bank. Je praat "
    "in het Nederlands, kort en concreet, met bankklant Lotte. Gebruik ALTIJD de "
    "beschikbare tools om cijfers op te vragen — verzin nooit bedragen of data. "
    "Leg het resultaat van een tool in gewone taal uit, zonder jargon. Dit is een "
    "proof-of-concept met fictieve data, geen echt financieel advies."
)


def call_claude_with_tools(
    customer_id: str,
    message: str,
    history: list[dict],
) -> tuple[str, list[str]]:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = [*history, {"role": "user", "content": message}]
    used_tools: list[str] = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            output_config={"effort": "low"},
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            text = next((b.text for b in response.content if b.type == "text"), "")
            return text, used_tools

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            used_tools.append(block.name)
            handler = TOOL_DISPATCH.get(block.name)
            try:
                if handler is None:
                    raise ValueError(f"Onbekende tool: {block.name}")
                result = handler(customer_id, **block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })
            except Exception as exc:  # noqa: BLE001 - fed back to the model, not raised
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(exc),
                    "is_error": True,
                })

        messages.append({"role": "user", "content": tool_results})

    return "Sorry, ik kon binnen de tijd geen volledig antwoord vinden.", used_tools

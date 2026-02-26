"""Thin API wrappers for Claude, Gemini, and GPT-5 with reasoning enabled."""

import os
from dataclasses import dataclass
from typing import List, Dict, Optional

import anthropic
import openai
from google import genai


@dataclass
class ModelResponse:
    model_id: str
    model_label: str
    content: str
    thinking: Optional[str] = None  # internal reasoning trace


class ClaudeModel:
    def __init__(self, model: str = "claude-opus-4-6", thinking_budget: int = 10000):
        self.client = anthropic.Anthropic()
        self.model = model
        self.label = "Claude"
        self.thinking_budget = thinking_budget

    def respond(self, system: str, messages: List[Dict]) -> ModelResponse:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            temperature=1,  # required for extended thinking
            thinking={
                "type": "adaptive",
            },
            system=system,
            messages=messages,
        )

        thinking = None
        content = ""
        for block in response.content:
            if block.type == "thinking":
                thinking = block.thinking
            elif block.type == "text":
                content = block.text

        return ModelResponse(
            model_id=self.model,
            model_label=self.label,
            content=content,
            thinking=thinking,
        )


class GeminiModel:
    def __init__(self, model: str = "gemini-3.1-pro-preview"):
        self.client = genai.Client()
        self.model = model
        self.label = "Gemini"

    def respond(self, system: str, messages: List[Dict]) -> ModelResponse:
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(genai.types.Content(
                role=role,
                parts=[genai.types.Part(text=msg["content"])],
            ))

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=genai.types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=8192,
                thinking_config=genai.types.ThinkingConfig(
                    thinking_level=genai.types.ThinkingLevel.HIGH,
                    include_thoughts=True,
                ),
            ),
        )

        # Extract thinking and response from parts
        thinking = None
        content = ""
        for part in response.candidates[0].content.parts:
            if part.thought:
                thinking = part.text
            else:
                content = part.text

        return ModelResponse(
            model_id=self.model,
            model_label=self.label,
            content=content,
            thinking=thinking,
        )


class OpenAIModel:
    def __init__(self, model: str = "gpt-5.2-2025-12-11", reasoning_effort: str = "high"):
        self.client = openai.OpenAI()
        self.model = model
        self.label = "GPT"
        self.reasoning_effort = reasoning_effort

    def respond(self, system: str, messages: List[Dict]) -> ModelResponse:
        oai_messages = [{"role": "system", "content": system}]
        for msg in messages:
            oai_messages.append({"role": msg["role"], "content": msg["content"]})

        response = self.client.responses.create(
            model=self.model,
            input=oai_messages,
            reasoning={"effort": self.reasoning_effort, "summary": "detailed"},
        )

        # Extract reasoning and response
        thinking = None
        content = ""
        for item in response.output:
            if item.type == "reasoning":
                # OpenAI returns reasoning summary when available
                if hasattr(item, "summary") and item.summary:
                    thinking = "\n".join(
                        s.text for s in item.summary if hasattr(s, "text")
                    )
            elif item.type == "message":
                content = item.content[0].text

        return ModelResponse(
            model_id=self.model,
            model_label=self.label,
            content=content,
            thinking=thinking,
        )


def get_default_models() -> list:
    """Return the three default models for the situation room."""
    return [
        ClaudeModel(),
        GeminiModel(),
        OpenAIModel(),
    ]

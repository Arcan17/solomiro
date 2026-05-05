"""AI provider abstraction layer supporting Anthropic, OpenAI, and Gemini."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI text generation providers."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a text response for the given prompt.

        Args:
            prompt: The input prompt string.

        Returns:
            Generated text response.
        """
        ...


class AnthropicProvider(AIProvider):
    """AI provider backed by Anthropic's Claude models."""

    def __init__(self, settings) -> None:
        """Initialize the Anthropic provider.

        Args:
            settings: Application settings containing AI_API_KEY and AI_MODEL.
        """
        import anthropic

        self._client = anthropic.AsyncAnthropic(api_key=settings.AI_API_KEY)
        self._model = settings.AI_MODEL

    async def generate(self, prompt: str) -> str:
        """Generate a response using the Anthropic Claude API.

        Args:
            prompt: The input prompt string.

        Returns:
            Generated text from Claude.
        """
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text


class OpenAIProvider(AIProvider):
    """AI provider backed by OpenAI's GPT models."""

    def __init__(self, settings) -> None:
        """Initialize the OpenAI provider.

        Args:
            settings: Application settings containing AI_API_KEY and AI_MODEL.
        """
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=settings.AI_API_KEY)
        self._model = settings.AI_MODEL

    async def generate(self, prompt: str) -> str:
        """Generate a response using the OpenAI API.

        Args:
            prompt: The input prompt string.

        Returns:
            Generated text from GPT.
        """
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content


class GeminiProvider(AIProvider):
    """AI provider backed by Google's Gemini models."""

    def __init__(self, settings) -> None:
        """Initialize the Gemini provider.

        Args:
            settings: Application settings containing AI_API_KEY and AI_MODEL.
        """
        import google.generativeai as genai

        genai.configure(api_key=settings.AI_API_KEY)
        self._model = genai.GenerativeModel(settings.AI_MODEL)

    async def generate(self, prompt: str) -> str:
        """Generate a response using the Gemini API.

        Args:
            prompt: The input prompt string.

        Returns:
            Generated text from Gemini.
        """
        response = self._model.generate_content(prompt)
        return response.text


class MockAIProvider(AIProvider):
    """Mock AI provider that returns fixed text, used for tests."""

    async def generate(self, prompt: str) -> str:
        """Return a fixed Spanish analysis string without calling any external API.

        Args:
            prompt: Ignored.

        Returns:
            Fixed placeholder text in Spanish.
        """
        return (
            '{"analyses": ['
            '"Análisis generado automáticamente para pruebas.", '
            '"Análisis generado automáticamente para pruebas.", '
            '"Análisis generado automáticamente para pruebas."'
            '], "general_verdict": "Veredicto generado automáticamente para pruebas."}'
        )


def get_ai_provider(settings) -> AIProvider:
    """Instantiate and return the configured AI provider.

    Args:
        settings: Application settings with AI_PROVIDER, AI_API_KEY, AI_MODEL.

    Returns:
        An instance of the appropriate AIProvider subclass.

    Raises:
        KeyError: If AI_PROVIDER is not one of anthropic, openai, gemini.
    """
    providers: dict[str, type[AIProvider]] = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
    }
    return providers[settings.AI_PROVIDER](settings)

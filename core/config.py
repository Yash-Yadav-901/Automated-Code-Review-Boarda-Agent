import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")


def get_groq_async_client() -> AsyncOpenAI:
    """Return an AsyncOpenAI client configured for Groq."""
    return AsyncOpenAI(
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
    )


def create_sk_kernel(service_id: str = "groq_chat") -> tuple[Kernel, OpenAIChatPromptExecutionSettings]:
    """Create and configure a Semantic Kernel instance with Groq AI service."""
    kernel = Kernel()
    client = get_groq_async_client()
    service = OpenAIChatCompletion(
        ai_model_id=GROQ_MODEL,
        async_client=client,
        service_id=service_id,
    )
    kernel.add_service(service)
    settings = OpenAIChatPromptExecutionSettings(
        temperature=0.2,
        max_tokens=1000,
    )
    return kernel, settings

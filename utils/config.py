"""Settings and LLM factory"""
import time
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.1
    MCP_SERVER_HOST: str = "localhost"
    MCP_SERVER_PORT: int = 8765

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


GROQ_FALLBACK = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "llama3-8b-8192",
]


def invoke_llm(messages: list, temperature: float = 0.1, max_tokens: int = 2048) -> str:
    """Invoke LLM with automatic fallback on rate limit."""
    s = get_settings()
    from langchain_groq import ChatGroq
    for model in GROQ_FALLBACK:
        try:
            llm = ChatGroq(model=model, temperature=temperature,
                           max_tokens=max_tokens, groq_api_key=s.GROQ_API_KEY)
            return llm.invoke(messages).content
        except Exception as e:
            err = str(e)
            if "429" in err or "rate_limit" in err.lower():
                print(f"[LLM] Rate limit on {model} — trying next")
                time.sleep(0.5)
                continue
            raise
    raise RuntimeError("All models rate-limited. Wait ~20 minutes.")

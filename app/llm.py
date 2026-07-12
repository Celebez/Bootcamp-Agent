"""Pembungkus LLM di sekeliling klien chat async yang kompatibel-OpenAI."""
from typing import List, Optional

from openai import AsyncOpenAI

from app.config import config
from app.schema import (
    ROLE_VALUES,
    Function,
    Message,
    ToolCall,
    ToolChoice,
)


class LLM:
    """Pembungkus async tipis yang mendukung chat biasa dan pemanggilan alat."""

    def __init__(self, config_name: str = "default"):
        llm_config = config.llm.get(config_name, config.llm["default"])
        self.model = llm_config.model
        self.max_tokens = llm_config.max_tokens
        self.temperature = llm_config.temperature
        self.api_key = llm_config.api_key
        self.base_url = llm_config.base_url
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    @staticmethod
    def format_messages(messages) -> List[dict]:
        formatted = []
        for m in messages:
            if isinstance(m, Message):
                m = m.to_dict()
            if isinstance(m, dict):
                if "role" not in m:
                    continue
                if "content" in m or "tool_calls" in m:
                    formatted.append(m)
        for msg in formatted:
            if msg["role"] not in ROLE_VALUES:
                raise ValueError(f"Peran tidak valid: {msg['role']}")
        return formatted

    async def ask(
        self,
        messages,
        system_msgs: Optional[List] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
    ) -> str:
        messages = (
            system_msgs + self.format_messages(messages)
            if system_msgs
            else self.format_messages(messages)
        )
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": self.max_tokens,
        }
        try:
            if stream:
                resp = await self.client.chat.completions.create(**params, stream=True)
                chunks = []
                async for chunk in resp:
                    delta = chunk.choices[0].delta.content or ""
                    chunks.append(delta)
                return "".join(chunks).strip()
            resp = await self.client.chat.completions.create(**params, stream=False)
            return resp.choices[0].message.content
        except Exception as e:  # jaringan / auth / rate-limit
            raise RuntimeError(f"Permintaan LLM gagal: {e}") from e

    async def ask_tool(
        self,
        messages,
        system_msgs: Optional[List] = None,
        tools=None,
        tool_choice: ToolChoice = ToolChoice.AUTO,
    ):
        messages = (
            system_msgs + self.format_messages(messages)
            if system_msgs
            else self.format_messages(messages)
        )
        params = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice.value if isinstance(tool_choice, ToolChoice) else tool_choice,
            "max_tokens": self.max_tokens,
        }
        try:
            resp = await self.client.chat.completions.create(**params)
        except Exception as e:  # jaringan / auth / rate-limit
            raise RuntimeError(f"Permintaan alat LLM gagal: {e}") from e
        msg = resp.choices[0].message

        class _Result:
            pass

        r = _Result()
        r.content = msg.content
        r.tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                r.tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        function=Function(name=tc.function.name, arguments=tc.function.arguments),
                    )
                )
        return r

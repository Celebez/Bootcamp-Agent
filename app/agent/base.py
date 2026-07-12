"""Agen dasar abstrak dengan loop eksekusi berbasis langkah."""
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import List, Optional

from pydantic import BaseModel, Field

from app.llm import LLM
from app.logger import logger
from app.schema import AgentState, Memory, Message


class BaseAgent(BaseModel, ABC):
    name: str = Field(..., description="Nama unik agen")
    description: Optional[str] = Field(None, description="Deskripsi agen opsional")

    system_prompt: Optional[str] = Field(None, description="Instruksi prompt sistem level-agensi")
    next_step_prompt: Optional[str] = Field(None, description="Prompt untuk langkah berikutnya")

    llm: LLM = Field(default_factory=LLM, description="Instance model bahasa")
    memory: Memory = Field(default_factory=Memory, description="Penyimpanan memori agen")
    state: AgentState = Field(default=AgentState.IDLE, description="Status saat ini")

    max_steps: int = Field(default=15, description="Langkah maksimum sebelum terminasi")
    current_step: int = Field(default=0, description="Langkah saat ini dalam eksekusi")
    duplicate_threshold: int = 2

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @asynccontextmanager
    async def state_context(self, new_state: AgentState):
        if not isinstance(new_state, AgentState):
            raise ValueError(f"Status tidak valid: {new_state}")
        previous_state = self.state
        self.state = new_state
        try:
            yield
        except Exception as e:
            self.state = AgentState.ERROR
            raise e
        finally:
            self.state = previous_state

    def update_memory(self, role, content: str, base64_image: Optional[str] = None, **kwargs):
        mapping = {
            "user": Message.user_message,
            "system": Message.system_message,
            "assistant": Message.assistant_message,
            "tool": lambda c, **kw: Message.tool_message(c, **kw),
        }
        if role not in mapping:
            raise ValueError(f"Peran pesan tidak didukung: {role}")
        kwargs = {"base64_image": base64_image, **(kwargs if role == "tool" else {})}
        self.memory.add_message(mapping[role](content, **kwargs))

    async def run(self, request: Optional[str] = None) -> str:
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Tidak dapat menjalankan agen dari status: {self.state}")
        if request:
            self.update_memory("user", request)

        results: List[str] = []
        async with self.state_context(AgentState.RUNNING):
            while self.current_step < self.max_steps and self.state != AgentState.FINISHED:
                self.current_step += 1
                logger.info(f"Menjalankan langkah {self.current_step}/{self.max_steps}")
                step_result = await self.step()
                if self.is_stuck():
                    self.handle_stuck_state()
                results.append(f"Langkah {self.current_step}: {step_result}")

            if self.current_step >= self.max_steps:
                self.state = AgentState.IDLE
                results.append(f"Dihentikan: Mencapai langkah maksimum ({self.max_steps})")
        return "\n".join(results) if results else "Tidak ada langkah yang dieksekusi"

    @abstractmethod
    async def step(self) -> str:
        pass

    def handle_stuck_state(self):
        stuck_prompt = "Mengamati respons duplikat. Pertimbangkan strategi baru dan hindari jalur yang tidak efektif."
        self.next_step_prompt = f"{stuck_prompt}\n{self.next_step_prompt}"

    def is_stuck(self) -> bool:
        if len(self.memory.messages) < 2:
            return False
        last = self.memory.messages[-1]
        if not last.content:
            return False
        dup = sum(
            1
            for m in reversed(self.memory.messages[:-1])
            if m.role == "assistant" and m.content == last.content
        )
        return dup >= self.duplicate_threshold

    @property
    def messages(self) -> List[Message]:
        return self.memory.messages

    @messages.setter
    def messages(self, value: List[Message]):
        self.memory.messages = value

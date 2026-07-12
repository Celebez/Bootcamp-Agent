"""Kelas dasar untuk alat."""
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    output: Any = Field(default=None)
    error: Optional[str] = Field(default=None)
    base64_image: Optional[str] = Field(default=None)

    class Config:
        arbitrary_types_allowed = True

    def __bool__(self):
        return any(getattr(self, f) for f in self.__fields__)

    def __str__(self):
        return f"Error: {self.error}" if self.error else str(self.output)

    def replace(self, **kwargs):
        return type(self)(**{**self.__dict__, **kwargs})


class BaseTool(ABC, BaseModel):
    name: str
    description: str
    parameters: Optional[dict] = None

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass

    async def __call__(self, **kwargs) -> Any:
        return await self.execute(**kwargs)

    def to_param(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or {},
            },
        }

    def success_response(self, data: Union[Dict[str, Any], str]) -> ToolResult:
        if isinstance(data, str):
            text = data
        else:
            text = json.dumps(data, indent=2)
        return ToolResult(output=text)

    def fail_response(self, msg: str) -> ToolResult:
        return ToolResult(error=msg)


class CLIResult(ToolResult):
    pass


class ToolFailure(ToolResult):
    pass

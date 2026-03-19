from __future__ import annotations

from pydantic import BaseModel, Field

ALLOWED_MODES = {"overwrite", "append"}


class FileWriteRequest(BaseModel):
    path: str = Field(..., min_length=1)
    content: str = Field(default="")
    mode: str = Field(default="overwrite")

    def model_post_init(self, __context: object) -> None:
        if self.mode not in ALLOWED_MODES:
            raise ValueError(f"mode must be one of {ALLOWED_MODES}")


class FileReadResponse(BaseModel):
    path: str
    content: str
    size_bytes: int


class FileListResponse(BaseModel):
    files: list[str]
    count: int


class FileDeleteResponse(BaseModel):
    deleted: bool
    path: str


class FileWriteResponse(BaseModel):
    ok: bool
    path: str

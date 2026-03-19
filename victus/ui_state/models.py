from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["info", "warning", "critical"]
WorkflowStatus = Literal["active", "paused", "completed"]


class Reminder(BaseModel):
    id: str
    title: str
    detail: str
    status: str = "pending"
    urgency: int = Field(default=50, ge=0, le=100)
    updated_at: int


class Approval(BaseModel):
    id: str
    title: str
    detail: str
    status: str = "pending"
    urgency: int = Field(default=50, ge=0, le=100)
    updated_at: int


class Alert(BaseModel):
    id: str
    title: str
    detail: str
    severity: Severity = "info"
    status: str = "open"
    urgency: int = Field(default=50, ge=0, le=100)
    updated_at: int


class Failure(BaseModel):
    id: str
    title: str
    detail: str
    severity: Severity = "critical"
    status: str = "open"
    urgency: int = Field(default=80, ge=0, le=100)
    updated_at: int


class Workflow(BaseModel):
    id: str
    title: str
    detail: str
    status: WorkflowStatus = "paused"
    urgency: int = Field(default=50, ge=0, le=100)
    progress: int = Field(default=0, ge=0, le=100)
    step: int = Field(default=1, ge=1)
    total_steps: int = Field(default=1, ge=1)
    updated_at: int


class FocusLaneCard(BaseModel):
    id: str
    kind: Literal["reminder", "approval", "alert", "failure", "workflow", "dialogue", "timeline"]


class DialogueMessage(BaseModel):
    id: str
    role: Literal["user", "system"]
    text: str
    created_at: int


class TimelineEvent(BaseModel):
    id: str
    label: str
    detail: str
    created_at: int


class UIState(BaseModel):
    reminders: list[Reminder]
    approvals: list[Approval]
    alerts: list[Alert]
    failures: list[Failure]
    workflows: list[Workflow]
    focus_lane_cards: list[FocusLaneCard]
    dialogue_messages: list[DialogueMessage]
    timeline_events: list[TimelineEvent]


class DialogueSendRequest(BaseModel):
    message: str


class WorkflowActionRequest(BaseModel):
    action: Literal["resume", "pause", "advance_step"]

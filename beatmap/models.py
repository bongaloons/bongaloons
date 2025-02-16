from pydantic import BaseModel
from typing import List, Optional, Literal


class GameStartInput(BaseModel):
    midi_file: str = "test.mid"


class WebSocketInput(BaseModel):
    key: Optional[str]
    type: Optional[Literal["end_game"]]


class FallingDot(BaseModel):
    move: str
    target_time: float
    track: str


class GameStartResponse(BaseModel):
    status: str
    duration: float
    falling_dots: List[FallingDot]


class GameStatusResponse(BaseModel):
    status: Literal["running", "not_running"]
    elapsed_time: Optional[float] = None
    total_duration: Optional[float] = None


class WebSocketHitResponse(BaseModel):
    type: Literal["hit_registered"]
    move: str
    time: float
    lastJudgement: str
    totalScore: int
    currentStreak: int
    maxStreak: int
    scoreDelta: int


class WebSocketGameOverResponse(BaseModel):
    type: Literal["game_over"]
    message: str
    totalScore: int


class HealthCheckResponse(BaseModel):
    status: Literal["ok"]

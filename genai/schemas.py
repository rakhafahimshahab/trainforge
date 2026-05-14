from typing import List

from pydantic import BaseModel, Field

class AIExercise(BaseModel):
    name: str = Field(description="Exercise name. Prefer items from the trainer's library when possible.")
    sets: int = Field(ge=1, le=12, description="Number of working sets")
    reps: str = Field(description="Rep target. Number or range (e.g. '8' or '8-10').")
    notes: str = Field(default="", description="One short cue or progression tip. Keep under 80 chars.")

class AIDay(BaseModel):
    day_label: str = Field(description="Short title for the day, e.g. 'Day 1 - Lower Body + Core'")
    focus: str = Field(description="What this session is targeting (e.g. 'Lower body strength')")
    exercises: List[AIExercise] = Field(min_length=2, max_length=10)

class AIPlanDraft(BaseModel):

    summary: str = Field(description="One-paragraph plain-text rationale for the overall plan.")
    days: List[AIDay] = Field(min_length=1, max_length=7)

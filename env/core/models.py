from pydantic import BaseModel
from typing import List, Optional


class Observation(BaseModel):
    code : str
    language : str
    task_id : str
    difficulty : str
    history : List[str]
    current_step : int
    max_steps : int
    available_actions : List[str]



class Action(BaseModel):
    action_type : str # identify issue, suggest a fix, implement the fix
    line_number : Optional[int] = None# where is the issue exactly, or in which line is the issue.
    issue_type : Optional[str] = None #oka set of issue types ani em undadu. Agent gets to know after certain iterations.
    suggestion : Optional[str] = None



class Internal_state(BaseModel):
    code: str
    language: str
    task_id: str
    difficulty: str
    true_issues: List[dict]
    identified_issues: List[dict]
    fixes_applied: List[dict]
    history: List[str]
    step_count: int
    max_steps: int
    done: bool

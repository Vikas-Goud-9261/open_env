from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class Observation(BaseModel):
    # Core code info
    code              : str
    language          : str
    task_id           : str
    difficulty        : str

    # Step tracking
    current_step      : int
    max_steps         : int

    # Agent's action history
    history           : List[Dict[str, Any]]  # was List[str], now full dict

    # What agent can do
    available_actions : List[str]

    # Agent's progress — was missing before
    identified_issues : List[Dict[str, Any]]
    fixes_applied     : List[Dict[str, Any]]

    # Bug progress info — was missing before
    total_bugs        : int
    bugs_addressed    : int
    can_approve       : bool


class Action(BaseModel):
    action_type  : str                    # identify_issue / suggest_fix / approve
    line_number  : Optional[int]  = None  # which line
    issue_type   : Optional[str]  = None  # type of bug
    description  : Optional[str]  = None  # agent's description of bug ← NEW
    suggestion   : Optional[str]  = None  # fix suggestion


class Internal_state(BaseModel):
    # Core code info
    code              : str
    language          : str
    task_id           : str
    difficulty        : str

    # Task ground truth
    true_issues       : List[Dict[str, Any]]

    # Agent's tracked progress
    identified_issues : List[Dict[str, Any]]
    fixes_applied     : List[Dict[str, Any]]

    # History — was List[str], now full dict
    history           : List[Dict[str, Any]]

    # Step tracking
    step_count        : int
    max_steps         : int
    done              : bool

    # Registry — the new core tracking system
    issue_registry    : Dict[int, Dict[str, Any]]  # ← NEW
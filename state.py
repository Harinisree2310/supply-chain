"""
state.py
----------
The State is the memory that flows through every node in the graph.
Each node reads from it and returns updates to it -- nothing is stored
anywhere else, which is what makes the agent's behavior traceable.
"""

from typing import TypedDict, List, Dict, Optional


class AgentState(TypedDict):
    disruption: Optional[Dict]        # the disruption currently being handled
    candidate_plans: List[Dict]       # all plans generated for this disruption
    valid_plans: List[Dict]           # plans that passed check_constraints
    chosen_plan: Optional[Dict]       # the plan the agent decided to execute
    justification: str                # LLM's explanation for the choice
    verification_passed: bool         # result of the verify step
    blocked_reasons: List[str]        # why verification failed, if it did
    excluded_vendor_ids: List[str]    # vendors ruled out after a failed attempt
    decision_log: List[str]           # human-readable trail of every step taken
    status: str                       # "monitoring" | "handling" | "blocked" | "resolved"
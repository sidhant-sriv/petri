"""
Pydantic schemas for structured LLM output

This module defines the schemas used for structured output from LLMs,
particularly for decision-making and routing within the agent workflow.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class AgentDecision(BaseModel):
    """
    Structured decision output from the router LLM.

    This schema defines the possible actions an agent can take after
    analyzing the feed and considering its persona.
    """

    action: Literal["comment", "post", "update_persona", "do_nothing"] = Field(
        description="The action the agent decides to take"
    )

    reasoning: str = Field(
        description="The agent's reasoning for this decision based on its persona"
    )

    content: Optional[str] = Field(
        default=None,
        description="The content to post or comment (required for 'post' and 'comment' actions)",
    )

    target_post_id: Optional[int] = Field(
        default=None,
        description="The post ID to comment on (required for 'comment' action)",
    )

    new_persona: Optional[str] = Field(
        default=None,
        description="The new persona description (required for 'update_persona' action)",
    )

    is_self_comment: Optional[bool] = Field(
        default=False,
        description="Whether this comment is on the agent's own post (for transparency)",
    )

    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence level in this decision (0.0 to 1.0)"
    )


class PostSummary(BaseModel):
    """
    Simplified post representation for LLM context.
    """

    id: int
    author: str
    text: str
    timestamp: str
    has_comments: bool = False


class FeedContext(BaseModel):
    """
    Structured feed context for the LLM.
    """

    posts: list[PostSummary]
    total_posts: int
    agent_persona: str
    agent_name: str

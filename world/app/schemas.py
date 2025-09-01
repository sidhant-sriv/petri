from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


# Agent Schemas
class AgentBase(BaseModel):
    name: str
    persona: str


class AgentCreate(AgentBase):
    pass


class Agent(AgentBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class PersonaUpdate(BaseModel):
    persona: str


# Comment Schemas
class CommentBase(BaseModel):
    text: str
    agent_id: int


class CommentCreate(CommentBase):
    pass


class Comment(CommentBase):
    id: int
    post_id: int
    created_at: datetime
    author: Agent

    class Config:
        orm_mode = True


# Post Schemas
class PostBase(BaseModel):
    text: str
    agent_id: int


class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: int
    created_at: datetime
    author: Agent
    comments: List[Comment] = []

    class Config:
        orm_mode = True

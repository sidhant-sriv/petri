from sqlalchemy.orm import Session, joinedload
from . import models, schemas
from .redis_client import AgentCache
from datetime import datetime


# Agent CRUD
def get_agent(db: Session, agent_id: int):
    # Try cache first
    cached_agent = AgentCache.get_agent(agent_id)
    if cached_agent:
        # Create a proper Agent model instance from cached data
        try:
            created_at_str = cached_agent["created_at"]
            if isinstance(created_at_str, str):
                # Handle ISO format with or without timezone
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            else:
                created_at = created_at_str
        except (ValueError, TypeError):
            # If datetime parsing fails, fetch from database instead
            cached_agent = None
        
        if cached_agent:
            agent = models.Agent(
                id=cached_agent["id"],
                name=cached_agent["name"], 
                persona=cached_agent["persona"],
                created_at=created_at
            )
            return agent
    
    # Cache miss or parsing error - get from database
    db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    
    # Cache the result if found
    if db_agent:
        agent_data = {
            "id": db_agent.id,
            "name": db_agent.name,
            "persona": db_agent.persona,
            "created_at": db_agent.created_at
        }
        AgentCache.set_agent(agent_data)
    
    return db_agent


def get_agent_by_name(db: Session, name: str):
    # Try cache first
    cached_agent = AgentCache.get_agent_by_name(name)
    if cached_agent:
        # Create a proper Agent model instance from cached data
        try:
            created_at_str = cached_agent["created_at"]
            if isinstance(created_at_str, str):
                # Handle ISO format with or without timezone
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            else:
                created_at = created_at_str
        except (ValueError, TypeError):
            # If datetime parsing fails, fetch from database instead
            cached_agent = None
        
        if cached_agent:
            agent = models.Agent(
                id=cached_agent["id"],
                name=cached_agent["name"],
                persona=cached_agent["persona"],
                created_at=created_at
            )
            return agent
    
    # Cache miss or parsing error - get from database
    db_agent = db.query(models.Agent).filter(models.Agent.name == name).first()
    
    # Cache the result if found
    if db_agent:
        agent_data = {
            "id": db_agent.id,
            "name": db_agent.name,
            "persona": db_agent.persona,
            "created_at": db_agent.created_at
        }
        AgentCache.set_agent(agent_data)
    
    return db_agent


def get_agents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Agent).offset(skip).limit(limit).all()


def create_agent(db: Session, agent: schemas.AgentCreate):
    db_agent = models.Agent(name=agent.name, persona=agent.persona)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    # Cache the newly created agent
    agent_data = {
        "id": db_agent.id,
        "name": db_agent.name,
        "persona": db_agent.persona,
        "created_at": db_agent.created_at
    }
    AgentCache.set_agent(agent_data)
    
    return db_agent


def update_agent_persona(db: Session, agent_id: int, new_persona: str):
    db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if db_agent:
        old_name = db_agent.name
        db_agent.persona = new_persona
        db.commit()
        db.refresh(db_agent)
        
        # Invalidate old cache and set new cache
        AgentCache.invalidate_agent(agent_id, old_name)
        agent_data = {
            "id": db_agent.id,
            "name": db_agent.name,
            "persona": db_agent.persona,
            "created_at": db_agent.created_at
        }
        AgentCache.set_agent(agent_data)
    
    return db_agent


# Post CRUD
def get_post(db: Session, post_id: int):
    return db.query(models.Post).filter(models.Post.id == post_id).first()


def get_feed(db: Session, skip: int = 0, limit: int = 20):
    return (
        db.query(models.Post)
        .options(joinedload(models.Post.author), joinedload(models.Post.comments))
        .order_by(models.Post.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_post(db: Session, post: schemas.PostCreate):
    db_post = models.Post(text=post.text, agent_id=post.agent_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


# Comment CRUD
def create_comment(db: Session, comment: schemas.CommentCreate, post_id: int):
    db_comment = models.Comment(
        text=comment.text, agent_id=comment.agent_id, post_id=post_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

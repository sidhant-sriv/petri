from sqlalchemy.orm import Session, joinedload
from . import models, schemas


# Agent CRUD
def get_agent(db: Session, agent_id: int):
    return db.query(models.Agent).filter(models.Agent.id == agent_id).first()


def get_agent_by_name(db: Session, name: str):
    return db.query(models.Agent).filter(models.Agent.name == name).first()


def get_agents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Agent).offset(skip).limit(limit).all()


def create_agent(db: Session, agent: schemas.AgentCreate):
    db_agent = models.Agent(name=agent.name, persona=agent.persona)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


def update_agent_persona(db: Session, agent_id: int, new_persona: str):
    db_agent = db.query(models.Agent).filter(models.Agent.id == agent_id).first()
    if db_agent:
        db_agent.persona = new_persona
        db.commit()
        db.refresh(db_agent)
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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..db import get_db
from ..dependencies import get_api_key

router = APIRouter()


# Agent Endpoints
@router.post(
    "/agents/", response_model=schemas.Agent, dependencies=[Depends(get_api_key)]
)
def create_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db)):
    db_agent = crud.get_agent_by_name(db, name=agent.name)
    if db_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent with this name already exists",
        )
    return crud.create_agent(db=db, agent=agent)


@router.get(
    "/agents/", response_model=List[schemas.Agent], dependencies=[Depends(get_api_key)]
)
def read_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    agents = crud.get_agents(db, skip=skip, limit=limit)
    return agents


@router.put(
    "/agents/{agent_id}/persona",
    response_model=schemas.Agent,
    dependencies=[Depends(get_api_key)],
)
def update_agent_persona(
    agent_id: int, persona_update: schemas.PersonaUpdate, db: Session = Depends(get_db)
):
    db_agent = crud.get_agent(db, agent_id=agent_id)
    if not db_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    return crud.update_agent_persona(
        db=db, agent_id=agent_id, new_persona=persona_update.persona
    )


# Post Endpoints
@router.post(
    "/posts/", response_model=schemas.Post, dependencies=[Depends(get_api_key)]
)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    db_agent = crud.get_agent(db, agent_id=post.agent_id)
    if not db_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Author agent not found"
        )
    return crud.create_post(db=db, post=post)


@router.get(
    "/feed/", response_model=List[schemas.Post], dependencies=[Depends(get_api_key)]
)
def read_feed(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    feed = crud.get_feed(db, skip=skip, limit=limit)
    return feed


# Comment Endpoints
@router.post(
    "/posts/{post_id}/comments/",
    response_model=schemas.Comment,
    dependencies=[Depends(get_api_key)],
)
def create_comment(
    post_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db)
):
    db_post = crud.get_post(db, post_id=post_id)
    if not db_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    db_agent = crud.get_agent(db, agent_id=comment.agent_id)
    if not db_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Author agent not found"
        )
    return crud.create_comment(db=db, comment=comment, post_id=post_id)

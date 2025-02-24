import logging
from collections.abc import Generator
from typing import Annotated
from sqlmodel import Session
from worker.core.db import engine

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

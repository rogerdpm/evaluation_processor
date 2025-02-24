import logging
from sqlmodel import Session, create_engine
from worker.core.config import settings
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=False)

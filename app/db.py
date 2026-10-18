"""Connection to the local SQLite database files (one for real data, one for sandbox)."""
from functools import lru_cache

from sqlmodel import Session, SQLModel, create_engine, select

from app.config import DB_FILES
from app.models import Category

DEFAULT_CATEGORIES = [
    ("Groceries", "expense"), ("Rent & home", "expense"), ("Bills & utilities", "expense"),
    ("Restaurants", "expense"), ("Leisure", "expense"), ("Transport", "expense"),
    ("Shopping", "expense"), ("Health", "expense"), ("Other expenses", "expense"),
    ("Salary", "income"), ("Other income", "income"), ("Transfers", "transfer"),
]


@lru_cache
def get_engine(mode: str):
    path = DB_FILES[mode]
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    _init(engine)
    return engine


def _init(engine) -> None:
    """Create the tables (only if missing) and the default categories."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        existing = set(session.exec(select(Category.name)).all())
        for name, kind in DEFAULT_CATEGORIES:
            if name not in existing:
                session.add(Category(name=name, kind=kind))
        session.commit()


def get_session(mode: str) -> Session:
    return Session(get_engine(mode))

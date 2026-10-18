"""Connection to the local SQLite database file."""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import Category

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///data/finance.db")
    prefix = "sqlite:///"
    if url.startswith(prefix) and not Path(url[len(prefix):]).is_absolute():
        # Make relative paths relative to the project folder, wherever the script is run from.
        path = ROOT / url[len(prefix):]
        path.parent.mkdir(parents=True, exist_ok=True)
        url = prefix + path.as_posix()
    return url


engine = create_engine(_database_url())

DEFAULT_CATEGORIES = [
    ("Groceries", "expense"), ("Rent & home", "expense"), ("Bills & utilities", "expense"),
    ("Restaurants", "expense"), ("Leisure", "expense"), ("Transport", "expense"),
    ("Shopping", "expense"), ("Health", "expense"), ("Other expenses", "expense"),
    ("Salary", "income"), ("Other income", "income"), ("Transfers", "transfer"),
]


def init_db() -> None:
    """Create the tables (only if they don't exist yet) and the default categories."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        existing = set(session.exec(select(Category.name)).all())
        for name, kind in DEFAULT_CATEGORIES:
            if name not in existing:
                session.add(Category(name=name, kind=kind))
        session.commit()


def get_session() -> Session:
    return Session(engine)

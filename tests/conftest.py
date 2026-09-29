import os

os.environ["LLM_CALL_GAP_SECONDS"] = "0"

import pytest

from app.database import Base, SessionLocal, engine
from app.routers.ravi import _provider_ready
from app.seed import seed_if_empty


@pytest.fixture(scope="session", autouse=True)
def seed_catalog() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: live LLM + DeepEval agent tests")


requires_agent = pytest.mark.skipif(
    not _provider_ready(),
    reason="Set LLM_PROVIDER and its API key in .env to run Ravi E2E tests",
)

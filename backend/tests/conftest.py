import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from backend.index import app
from backend.src.database import get_db
from backend.src.models.project import Base


TEST_DB_URL = "sqlite:///./test_app.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def project(client):
    resp = client.post("/api/projects", json={"name": "Test Project", "system_type": "LIMS"})
    assert resp.status_code == 200
    return resp.json()


MOCK_SAP = {
    "system_description": "LIMS system for sample tracking",
    "gamp5_category": "Category 4",
    "intended_uses": ["sample tracking", "audit logging"],
    "assurance_strategy": "Scripted testing for high-risk functions",
}

MOCK_PRA = {
    "risk_classifications": [
        {"feature": "Login", "risk_classification": "High Risk"},
        {"feature": "Report Export", "risk_classification": "Not High Risk"},
    ],
    "total_features": 2,
    "high_risk_count": 1,
    "not_high_risk_count": 1,
}

MOCK_RTM = {
    "requirements": [
        {"req_id": "URS-001", "description": "System shall log user actions", "test_refs": ["TC-001"]}
    ]
}

MOCK_STP = {
    "test_cases": [
        {"tc_id": "TC-001", "description": "Verify login audit trail", "steps": ["Login", "Check log"]}
    ]
}

MOCK_UTR = {
    "test_records": [
        {"tr_id": "TR-001", "description": "Exploratory test of report export"}
    ]
}

MOCK_ASR = {
    "overall_conclusion": "System is fit for intended use",
    "coverage_summary": "All high-risk requirements tested",
    "system_fitness": "Validated",
}

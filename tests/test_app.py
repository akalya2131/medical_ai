from pathlib import Path

import pytest

from app import create_app
from app.models import PatientRecord, User, db


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    model_path = tmp_path / "risk_model.joblib"
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
            "MODEL_PATH": str(model_path),
        }
    )

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
    if Path(model_path).exists():
        Path(model_path).unlink()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, email="doctor@example.com", password="strongpass123"):
    return client.post(
        "/register",
        data={
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )


def login(client, email="doctor@example.com", password="strongpass123"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def test_register_login_and_dashboard_access(client):
    response = register(client)
    assert b"Registration successful" in response.data

    response = login(client)
    assert b"Patient risk dashboard" in response.data

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert b"Total Patients" in dashboard.data


def test_duplicate_email_is_rejected(client):
    register(client)
    response = register(client)
    assert b"already exists" in response.data


def test_prediction_creates_patient_record(client, app):
    register(client)
    login(client)

    response = client.post(
        "/predict",
        data={
            "patient_name": "Jane Doe",
            "age": "62",
            "bmi": "31.5",
            "smoking_status": "smoker",
        },
        follow_redirects=True,
    )

    assert b"Prediction Result" in response.data
    assert b"Elevated Cardiometabolic Risk" in response.data or b"Stable Cardiometabolic Profile" in response.data

    with app.app_context():
        record = PatientRecord.query.filter_by(patient_name="Jane Doe").first()
        assert record is not None
        assert record.user.email == "doctor@example.com"
        assert record.risk_level in {"High", "Low"}
        assert record.probability >= 0


def test_patient_filters_render_correct_records(client, app):
    register(client)
    login(client)

    with app.app_context():
        user = User.query.filter_by(email="doctor@example.com").first()
        db.session.add(
            PatientRecord(
                user_id=user.id,
                patient_name="High Risk Patient",
                age=60,
                bmi=34.0,
                smoking_status="smoker",
                risk_level="High",
                probability=88.5,
                predicted_disease="Elevated Cardiometabolic Risk",
                explanation="High risk due to combined factors.",
                preventive_suggestions="Seek follow-up.",
            )
        )
        db.session.add(
            PatientRecord(
                user_id=user.id,
                patient_name="Low Risk Patient",
                age=25,
                bmi=21.0,
                smoking_status="non-smoker",
                risk_level="Low",
                probability=12.0,
                predicted_disease="Stable Cardiometabolic Profile",
                explanation="Low risk profile.",
                preventive_suggestions="Maintain healthy habits.",
            )
        )
        db.session.commit()

    high_risk = client.get("/patients?risk=high")
    assert b"High Risk Patient" in high_risk.data
    assert b"Low Risk Patient" not in high_risk.data

    low_risk = client.get("/patients?risk=low")
    assert b"Low Risk Patient" in low_risk.data
    assert b"High Risk Patient" not in low_risk.data

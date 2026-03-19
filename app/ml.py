from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.utils import build_explanation, build_preventive_suggestions, smoking_to_binary


def train_model(model_path):
    rng = np.random.default_rng(42)

    sample_count = 1800
    ages = rng.integers(18, 91, sample_count)
    bmis = rng.uniform(16.0, 42.0, sample_count)
    smokers = rng.binomial(1, 0.28, sample_count)

    linear_score = (
        -7.6
        + (ages * 0.065)
        + (bmis * 0.12)
        + (smokers * 1.5)
        + np.where(ages > 55, 0.7, 0.0)
        + np.where(bmis > 30, 0.8, 0.0)
    )
    probabilities = 1 / (1 + np.exp(-linear_score))
    labels = rng.binomial(1, probabilities)

    features = np.column_stack([ages, bmis, smokers])
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=500)),
        ]
    )
    pipeline.fit(features, labels)

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    return pipeline


def ensure_model(model_path):
    model_path = Path(model_path)
    if model_path.exists():
        return joblib.load(model_path)
    return train_model(model_path)


def predict_patient(age, bmi, smoking_status, model_path):
    model = ensure_model(model_path)
    feature_row = np.array([[age, bmi, smoking_to_binary(smoking_status)]], dtype=float)

    probability = float(model.predict_proba(feature_row)[0][1] * 100)
    prediction = int(model.predict(feature_row)[0])
    risk_level = "High" if prediction == 1 else "Low"
    predicted_disease = (
        "Elevated Cardiometabolic Risk"
        if risk_level == "High"
        else "Stable Cardiometabolic Profile"
    )

    explanation = build_explanation(age, bmi, smoking_status, probability)
    preventive_suggestions = build_preventive_suggestions(age, bmi, smoking_status, risk_level)

    return {
        "risk_level": risk_level,
        "probability": probability,
        "predicted_disease": predicted_disease,
        "explanation": explanation,
        "preventive_suggestions": preventive_suggestions,
    }

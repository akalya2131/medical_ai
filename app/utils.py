from functools import wraps

from flask import flash, g, redirect, url_for


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


def normalize_email(email):
    return (email or "").strip().lower()


def smoking_to_binary(smoking_status):
    return 1 if smoking_status == "smoker" else 0


def build_explanation(age, bmi, smoking_status, probability):
    factors = []
    if smoking_status == "smoker":
        factors.append("active smoking adds measurable strain to cardiovascular and metabolic health")
    if bmi >= 25:
        factors.append("an elevated BMI suggests higher metabolic load")
    if age >= 45:
        factors.append("age increases baseline cardiometabolic vulnerability")

    if len(factors) >= 2:
        combined = " The combined effect of multiple risk factors raises the overall probability more than any one factor alone."
    else:
        combined = ""

    if factors:
        joined = "; ".join(factors)
        return (
            f"The model estimated a {probability:.1f}% cardiometabolic risk because {joined}."
            f"{combined}"
        )

    return (
        f"The model estimated a {probability:.1f}% cardiometabolic risk with no major flagged drivers "
        "beyond the baseline profile from age, BMI, and smoking status."
    )


def build_preventive_suggestions(age, bmi, smoking_status, risk_level):
    suggestions = []
    if smoking_status == "smoker":
        suggestions.append("Prioritize a smoking cessation plan and clinical support to reduce risk quickly.")
    if bmi >= 25:
        suggestions.append("Aim for gradual weight reduction with structured nutrition and regular physical activity.")
    if age >= 45:
        suggestions.append("Schedule periodic blood pressure, glucose, and lipid screening with a clinician.")
    if risk_level == "Low":
        suggestions.append("Maintain current healthy habits with consistent exercise, sleep, and balanced nutrition.")
    else:
        suggestions.append("Follow up with a healthcare professional for a fuller risk assessment and prevention plan.")

    return " ".join(dict.fromkeys(suggestions))


def risk_label_to_filter(risk_value):
    if risk_value == "high":
        return "High"
    if risk_value == "low":
        return "Low"
    return None

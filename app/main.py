from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import func

from app.ml import predict_patient
from app.models import PatientRecord, db
from app.utils import login_required, risk_label_to_filter

main_bp = Blueprint("main", __name__)


def get_user_record(record_id):
    record = PatientRecord.query.filter_by(id=record_id, user_id=g.user.id).first()
    if record is None:
        abort(404)
    return record


@main_bp.route("/dashboard")
@login_required
def dashboard():
    records = PatientRecord.query.filter_by(user_id=g.user.id)

    total_patients = records.count()
    high_risk_count = records.filter_by(risk_level="High").count()
    low_risk_count = records.filter_by(risk_level="Low").count()
    average_bmi = (
        db.session.query(func.avg(PatientRecord.bmi))
        .filter(PatientRecord.user_id == g.user.id)
        .scalar()
        or 0.0
    )
    recent_patients = (
        PatientRecord.query.filter_by(user_id=g.user.id)
        .order_by(PatientRecord.created_at.desc())
        .limit(5)
        .all()
    )

    chart_data = {
        "labels": ["High Risk", "Low Risk"],
        "datasets": [
            {
                "data": [high_risk_count, low_risk_count],
                "backgroundColor": ["#38bdf8", "#93c5fd"],
                "borderColor": ["#0f172a", "#1e3a8a"],
                "borderWidth": 2,
            }
        ],
    }

    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        high_risk_count=high_risk_count,
        low_risk_count=low_risk_count,
        average_bmi=round(average_bmi, 1),
        recent_patients=recent_patients,
        chart_data=chart_data,
    )


@main_bp.route("/predict", methods=("GET", "POST"))
@login_required
def predict():
    if request.method == "POST":
        patient_name = (request.form.get("patient_name") or "").strip()
        age_raw = request.form.get("age", "").strip()
        bmi_raw = request.form.get("bmi", "").strip()
        smoking_status = request.form.get("smoking_status", "").strip()

        error = None
        try:
            age = int(age_raw)
        except ValueError:
            age = None
        try:
            bmi = float(bmi_raw)
        except ValueError:
            bmi = None

        if not patient_name:
            error = "Patient name is required."
        elif len(patient_name) > 120:
            error = "Patient name must be 120 characters or fewer."
        elif age is None or not 18 <= age <= 100:
            error = "Age must be between 18 and 100."
        elif bmi is None or not 10 <= bmi <= 60:
            error = "BMI must be between 10 and 60."
        elif smoking_status not in {"smoker", "non-smoker"}:
            error = "Smoking status must be selected."

        if error is not None:
            flash(error, "error")
            return render_template("predict.html", form_data=request.form)

        prediction = predict_patient(age, bmi, smoking_status, current_app.config["MODEL_PATH"])
        record = PatientRecord(
            user_id=g.user.id,
            patient_name=patient_name,
            age=age,
            bmi=bmi,
            smoking_status=smoking_status,
            risk_level=prediction["risk_level"],
            probability=prediction["probability"],
            predicted_disease=prediction["predicted_disease"],
            explanation=prediction["explanation"],
            preventive_suggestions=prediction["preventive_suggestions"],
        )
        db.session.add(record)
        db.session.commit()
        flash("Prediction complete.", "success")
        return redirect(url_for("main.result", record_id=record.id))

    return render_template("predict.html", form_data={})


@main_bp.route("/result/<int:record_id>")
@login_required
def result(record_id):
    record = get_user_record(record_id)
    return render_template("result.html", record=record)


@main_bp.route("/patients")
@login_required
def patients():
    active_filter = request.args.get("risk", "").lower()
    risk_filter = risk_label_to_filter(active_filter)

    query = PatientRecord.query.filter_by(user_id=g.user.id)
    if risk_filter:
        query = query.filter_by(risk_level=risk_filter)

    patient_records = query.order_by(PatientRecord.created_at.desc()).all()
    return render_template(
        "patients.html",
        patient_records=patient_records,
        active_filter=active_filter if risk_filter else "all",
    )


@main_bp.route("/new-prediction")
@login_required
def new_prediction():
    return redirect(url_for("main.predict"))

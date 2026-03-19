document.addEventListener("DOMContentLoaded", () => {
    setupFlashDismiss();
    setupValidation();
    setupLoadingOverlay();
    setupRiskChart();
});

function setupFlashDismiss() {
    const container = document.getElementById("flashContainer");
    if (!container) {
        return;
    }

    container.querySelectorAll(".flash-close").forEach((button) => {
        button.addEventListener("click", () => {
            const flash = button.closest(".flash-item");
            hideFlash(flash);
        });
    });

    window.setTimeout(() => {
        container.querySelectorAll(".flash-item").forEach((flash) => hideFlash(flash));
    }, 4500);
}

function hideFlash(flash) {
    if (!flash || flash.classList.contains("flash-hide")) {
        return;
    }
    flash.classList.add("flash-hide");
    window.setTimeout(() => flash.remove(), 220);
}

function setupValidation() {
    document.querySelectorAll("form[data-validate]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const invalidField = [...form.elements].find((field) => {
                if (typeof field.checkValidity !== "function") {
                    return false;
                }
                return !field.checkValidity();
            });

            if (invalidField) {
                event.preventDefault();
                invalidField.reportValidity();
                invalidField.focus();
            }
        });
    });
}

function setupLoadingOverlay() {
    const overlay = document.getElementById("loadingOverlay");
    if (!overlay) {
        return;
    }

    document.querySelectorAll("form[data-loading='prediction']").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (!form.checkValidity()) {
                return;
            }

            const patientName = form.querySelector("[name='patient_name']");
            const smokingStatus = form.querySelector("[name='smoking_status']");
            if (!patientName?.value.trim() || !smokingStatus?.value) {
                event.preventDefault();
                return;
            }

            overlay.classList.remove("hidden");
            overlay.classList.add("flex");
        });
    });
}

function setupRiskChart() {
    const canvas = document.getElementById("riskChart");
    if (!canvas || typeof Chart === "undefined" || !window.chartPayload) {
        return;
    }

    const data = window.chartPayload;
    new Chart(canvas, {
        type: "doughnut",
        data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "72%",
            plugins: {
                legend: {
                    labels: {
                        color: "#e2e8f0",
                        usePointStyle: true,
                        padding: 18,
                        font: {
                            family: "Poppins",
                        },
                    },
                },
                tooltip: {
                    backgroundColor: "rgba(15, 23, 42, 0.92)",
                    borderColor: "rgba(255, 255, 255, 0.12)",
                    borderWidth: 1,
                    titleColor: "#f8fafc",
                    bodyColor: "#cbd5e1",
                },
            },
        },
    });
}

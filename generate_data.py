import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
conn = sqlite3.connect("hospital_billing.db")
cursor = conn.cursor()

# Clear old data
cursor.execute("DELETE FROM Insurance_Claims")
cursor.execute("DELETE FROM Billing_Revenue")
cursor.execute("DELETE FROM Patient_Visit_Info")

# -----------------------------
# SETTINGS
# -----------------------------
TOTAL_RECORDS = 8000

departments = [
    "ICU",
    "OPD",
    "Pharmacy",
    "Radiology",
    "Surgery"
]

visit_types = [
    "OPD",
    "IPD",
    "ER"
]

payment_modes = [
    "Self-Pay",
    "Private Insurance",
    "Govt Health Schemes"
]

insurance_providers = [
    "Star Health",
    "HDFC ERGO",
    "ICICI Lombard",
    "Niva Bupa",
    "Care Health",
    "Government Health Scheme"
]

denial_reasons = [
    "Incorrect ICD/CPT Coding",
    "Missing Documents",
    "Late Submission",
    "Coverage Expired"
]

delay_reasons = [
    "Missing Doctor Signature",
    "Missing Documents",
    "Coding Review",
    "Late Submission"
]

procedures = {
    "ICU": [
        "Critical Care",
        "ICU Consultation",
        "Ventilator Support",
        "ICU Monitoring"
    ],
    "OPD": [
        "General Consultation",
        "Specialist Consultation",
        "Follow-up Visit",
        "Health Check-up"
    ],
    "Pharmacy": [
        "Prescription Medicines",
        "Emergency Medicines",
        "Chronic Medicines",
        "Post-discharge Medicines"
    ],
    "Radiology": [
        "MRI Scan",
        "CT Scan",
        "X-Ray",
        "Ultrasound"
    ],
    "Surgery": [
        "Minor Surgery",
        "Major Surgery",
        "Laparoscopic Surgery",
        "Orthopedic Surgery"
    ]
}

# Data covers 18 months
today = datetime.today().date()
start_date = today - timedelta(days=18 * 30)

# -----------------------------
# GENERATE DATA
# -----------------------------

for i in range(1, TOTAL_RECORDS + 1):

    patient_id = f"P{100000 + i}"
    bill_id = f"B{200000 + i}"

    visit_type = random.choices(
        visit_types,
        weights=[60, 25, 15]
    )[0]

    department = random.choices(
        departments,
        weights=[12, 35, 18, 15, 20]
    )[0]

    admission_date = start_date + timedelta(
        days=random.randint(0, (today - start_date).days)
    )

    # Discharge based on visit type
    if visit_type == "IPD":
        stay_days = random.randint(1, 14)
    elif visit_type == "ER":
        stay_days = random.randint(0, 2)
    else:
        stay_days = 0

    discharge_date = admission_date + timedelta(days=stay_days)

    procedure = random.choice(procedures[department])

    # -----------------------------
    # BILLING AMOUNT
    # -----------------------------

    amount_ranges = {
        "ICU": (35000, 180000),
        "Surgery": (45000, 250000),
        "Radiology": (2500, 35000),
        "Pharmacy": (800, 25000),
        "OPD": (500, 15000)
    }

    minimum, maximum = amount_ranges[department]

    gross_amount = round(
        random.uniform(minimum, maximum), 2
    )

    # -----------------------------
    # UNBILLED
    # -----------------------------

    if random.random() < 0.13:

        unbilled_amount = round(
            gross_amount * random.uniform(0.03, 0.30),
            2
        )

        billing_status = random.choice([
            "Unbilled",
            "Pending"
        ])

        delay_reason = random.choice(delay_reasons)

    else:

        unbilled_amount = 0

        billing_status = random.choices(
            ["Billed", "Pending"],
            weights=[90, 10]
        )[0]

        delay_reason = "N/A"

    # -----------------------------
    # PAYMENT MODE
    # -----------------------------

    payment_mode = random.choices(
        payment_modes,
        weights=[40, 45, 15]
    )[0]

    # -----------------------------
    # PAYMENT LAG
    # -----------------------------

    payment_lag = random.randint(0, 30)

    if payment_mode == "Private Insurance":
        payment_lag += random.randint(3, 15)

    elif payment_mode == "Govt Health Schemes":
        payment_lag += random.randint(8, 25)

    if billing_status in ["Pending", "Unbilled"]:
        payment_lag += random.randint(5, 20)

    payment_lag = min(payment_lag, 90)

    # -----------------------------
    # BILLING DATE
    # -----------------------------

    billing_date = discharge_date + timedelta(
        days=random.randint(0, 4)
    )

    if billing_date > today:
        billing_date = today

    # -----------------------------
    # INSERT PATIENT
    # -----------------------------

    cursor.execute("""
    INSERT INTO Patient_Visit_Info
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        patient_id,
        visit_type,
        department,
        admission_date,
        discharge_date,
        procedure
    ))

    # -----------------------------
    # INSERT BILL
    # -----------------------------

    cursor.execute("""
    INSERT INTO Billing_Revenue
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        bill_id,
        patient_id,
        gross_amount,
        unbilled_amount,
        billing_status,
        payment_lag,
        payment_mode,
        billing_date,
        delay_reason
    ))

    # -----------------------------
    # CLAIM
    # -----------------------------

    if payment_mode != "Self-Pay" and random.random() < 0.88:

        claim_id = f"C{300000 + i}"

        provider = (
            "Government Health Scheme"
            if payment_mode == "Govt Health Schemes"
            else random.choice(insurance_providers[:-1])
        )

        claim_amount = round(
            (gross_amount - unbilled_amount)
            * random.uniform(0.65, 1.0),
            2
        )

        claim_status = random.choices(
            ["Approved", "Denied", "Pending"],
            weights=[76, 11, 13]
        )[0]

        if claim_status == "Denied":

            denial_reason = random.choice(denial_reasons)

            resolution_date = billing_date + timedelta(
                days=random.randint(3, 35)
            )

            if resolution_date > today:
                resolution_date = today

        elif claim_status == "Pending":

            denial_reason = "N/A"
            resolution_date = None

        else:

            denial_reason = "N/A"

            resolution_date = billing_date + timedelta(
                days=random.randint(2, 25)
            )

            if resolution_date > today:
                resolution_date = today

        submission_date = billing_date + timedelta(
            days=random.randint(0, 8)
        )

        if submission_date > today:
            submission_date = today

        cursor.execute("""
        INSERT INTO Insurance_Claims
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            claim_id,
            bill_id,
            patient_id,
            provider,
            claim_amount,
            claim_status,
            denial_reason,
            submission_date,
            resolution_date
        ))

# -----------------------------
# SAVE
# -----------------------------

conn.commit()

# Check counts
cursor.execute("SELECT COUNT(*) FROM Patient_Visit_Info")
patient_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Billing_Revenue")
billing_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM Insurance_Claims")
claim_count = cursor.fetchone()[0]

conn.close()

print("--------------------------------")
print("DATA GENERATION COMPLETED")
print("--------------------------------")
print("Patient/Visit records:", patient_count)
print("Billing records:", billing_count)
print("Claim records:", claim_count)
print("--------------------------------")
print("Database: hospital_billing.db")
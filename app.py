import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random

# Initialize SQLite database
conn = sqlite3.connect('patient_data.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS patients 
             (patient_id TEXT, name TEXT, is_international INTEGER, insurance_balance REAL, 
              subjective TEXT, objective TEXT, assessment TEXT, plan TEXT, follow_up TEXT, timestamp TEXT)''')
conn.commit()

# Mock dataset for 30 patients
mock_patients = {
    f"P{i:03d}": {
        "name": f"Patient {i}",
        "is_international": random.choice([0, 1]),
        "balance": random.uniform(200, 1000),
        "historical_visits": random.randint(1, 5)
    } for i in range(1, 31)
}
mock_patients["P001"] = {"name": "Raj Kumar", "is_international": 1, "balance": 500.0, "historical_visits": 3}

# Mock historical conditions for Raj
raj_history = [
    {"timestamp": "2025-08-01", "assessment": "Seasonal allergic rhinitis", "body_part": "Respiratory"},
    {"timestamp": "2025-08-10", "assessment": "Sinus congestion", "body_part": "Respiratory"},
    {"timestamp": "2025-08-20", "assessment": "Asthma-like symptoms", "body_part": "Respiratory"}
]

# Mock pollen forecast (simulates external API)
pollen_forecast = {"today": "High", "in_7_days": "Moderate"}

# Function to parse transcript into SOAP (rule-based, mimics LLM)
def parse_transcript(transcript):
    if not transcript.strip():
        return "No input provided.", "No vitals recorded.", "Unable to diagnose.", "Refer to physician."
    
    subjective = objective = assessment = plan = ""
    if "stuffy nose" in transcript.lower() or "itchy eyes" in transcript.lower():
        subjective = "Patient reports nasal congestion, itchy eyes for 14 days, worse outdoors. No fever, no med allergies. Tried saline spray."
        objective = "BP 118/76, HR 82, temp 36.8°C. Mild nasal erythema, clear rhinorrhea."
        assessment = "Seasonal allergic rhinitis, mild-moderate."
        plan = "Prescribe loratadine 10mg daily x14 days. Recommend saline irrigation, OTC eye drops. Follow up 7-10 days."
    else:
        subjective = "Unknown symptoms reported."
        objective = "No vitals recorded."
        assessment = "Unable to diagnose."
        plan = "Refer to physician."
    return subjective, objective, assessment, plan

# Function for predictive follow-up and health risk analysis
def analyze_patient(patient_id, assessment):
    follow_up = ""
    health_risk = ""
    
    # Check visit frequency
    c.execute("SELECT timestamp FROM patients WHERE patient_id = ?", (patient_id,))
    visits = c.fetchall()
    if len(visits) >= 3:
        dates = [datetime.strptime(v[0], "%Y-%m-%d %H:%M:%S") for v in visits]
        if len(dates) >= 3 and (max(dates) - min(dates)).days <= 14:
            follow_up = "Frequent visits (3+ in 2 weeks). Recommend booking doctor consultation."
    
    # Health risk for Raj
    if patient_id == "P001":
        body_parts = [h["body_part"] for h in raj_history]
        if body_parts.count("Respiratory") >= 2:
            health_risk = "Recurring respiratory issues detected. Consider specialist referral for further evaluation."
    
    # Add pollen-based follow-up
    if "allergic rhinitis" in assessment.lower() and pollen_forecast["in_7_days"] == "Moderate":
        follow_up += " Reassess in 7 days due to moderate pollen forecast."
    
    return follow_up.strip() or "No specific follow-up needed.", health_risk

# Function to check insurance and calculate costs
def check_insurance(patient_id, plan):
    if patient_id in mock_patients:
        if mock_patients[patient_id]["is_international"]:
            balance = mock_patients[patient_id]["balance"]
            cost = 20.0  # Assume loratadine costs $20
            covered = min(balance, cost * 0.5)
            out_of_pocket = cost - covered
            new_balance = balance - covered
            mock_patients[patient_id]["balance"] = new_balance
            return f"International student. Insurance balance: ${new_balance:.2f}. Out-of-pocket: ${out_of_pocket:.2f}."
        return f"Non-international patient. Insurance balance: ${mock_patients[patient_id]['balance']:.2f}."
    return "No insurance data found."

# Custom CSS for Myntra-inspired UI with MedMe colors
st.markdown("""
<style>
    .stApp {
        background-color: #F5F7FA;
        font-family: 'Arial', sans-serif;
    }
    .stTextInput, .stTextArea {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #005B99;
    }
    .stButton>button {
        background-color: #00A886;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #008A6B;
    }
    .card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1, h2, h3 {
        color: #005B99;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Streamlit UI
st.title("MedMe AI Clinical Assistant Demo")

# Input section
st.markdown('<div class="card">', unsafe_allow_html=True)
patient_id = st.text_input("Patient ID", "P001", help="Enter a patient ID (e.g., P001 for Raj Kumar)")
transcript = st.text_area("Consultation Transcript", "Patient: Stuffy nose, itchy eyes for two weeks. Pharmacist: Any allergies? Patient: No.", help="Enter consultation text")
st.markdown('</div>', unsafe_allow_html=True)

# Process button
if st.button("Process Consultation"):
    if not patient_id or patient_id not in mock_patients:
        st.error("Invalid or missing Patient ID. Try P001–P030.")
    else:
        # Parse transcript
        subjective, objective, assessment, plan = parse_transcript(transcript)
        follow_up, health_risk = analyze_patient(patient_id, assessment)
        insurance_status = check_insurance(patient_id, plan)

        # Store in database
        c.execute("INSERT INTO patients (patient_id, name, is_international, insurance_balance, subjective, objective, assessment, plan, follow_up, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (patient_id, mock_patients.get(patient_id, {}).get("name", "Unknown"),
                   mock_patients.get(patient_id, {}).get("is_international", 0),
                   mock_patients.get(patient_id, {}).get("balance", 0.0),
                   subjective, objective, assessment, plan, follow_up, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

        # Display SOAP note
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("SOAP Note")
        st.write(f"**Subjective**: {subjective}")
        st.write(f"**Objective**: {objective}")
        st.write(f"**Assessment**: {assessment}")
        st.write(f"**Plan**: {plan}")
        st.write(f"**Predictive Follow-Up**: {follow_up}")
        if health_risk:
            st.warning(f"**Health Risk Alert**: {health_risk}")
        st.write(f"**Insurance Status**: {insurance_status}")
        st.markdown('</div>', unsafe_allow_html=True)

# Display patient history
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Patient History")
if patient_id and patient_id in mock_patients:
    c.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    history = c.fetchall()
    if history:
        df = pd.DataFrame(history, columns=["ID", "Name", "International", "Balance", "Subjective", "Objective", "Assessment", "Plan", "Follow-Up", "Timestamp"])
        st.dataframe(df[["Timestamp", "Subjective", "Assessment", "Plan", "Follow-Up"]], use_container_width=True)
    else:
        st.info("No prior consultations found for this patient.")
else:
    st.info("Enter a valid Patient ID to view history.")
st.markdown('</div>', unsafe_allow_html=True)

# Close database
conn.close()

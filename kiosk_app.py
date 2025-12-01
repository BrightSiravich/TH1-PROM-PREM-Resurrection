# --- Page Configuration ---
st.set_page_config(
    page_title="Patient Visit Form",
    layout="wide"
)
import streamlit as st
import pandas as pd
from datetime import datetime
import db_utils as db
import calculations as calc
import odi_content as odi_content



# --- Helper Functions ---
def calculate_odi(scores):
    """
    Calculates the Oswestry Disability Index (ODI) score.
    Formula: (Sum of scores / (Number of questions answered * 5)) * 100
    Each question is scored 0-5.
    """
    valid_scores = [s for s in scores if s is not None]
    
    if len(valid_scores) < 7:
        return None
        
    total_score = sum(valid_scores)
    max_possible_score = len(valid_scores) * 5
    
    if max_possible_score == 0:
        return 0.0
        
    return (total_score / max_possible_score) * 100 

# --- Main Application ---

if 'submitted' not in st.session_state:
    st.session_state.submitted = False

if st.session_state.submitted:
    st.success("Thank you! The patient visit has been recorded.")
    if st.button("Reload for Next Patient", type="primary"):
        st.session_state.submitted = False
        st.rerun()
else:
    st.title("Add New Patient Visit")
    
    # Procedure Type Selector
    st.markdown("#### Procedure Info")
    proc_type = st.radio("Procedure Type", ["TL Spine Procedure", "C Spine Procedure"], horizontal=True)
    
    # 1. Patient Info
    st.markdown("#### Patient Details")
    col1, col2 = st.columns(2)
    with col1:
        hn = st.text_input("HN (Hospital Number)")
        gender = st.selectbox("Gender", ["Male", "Female"])
    with col2:
        visit_date = st.date_input("Visit Date", datetime.now())
        age = st.number_input("Age", min_value=0, max_value=120, step=1)

    # 2. Operation Info
    st.markdown("#### Operation Info")
    
    col3, col4 = st.columns(2)
    with col3:
        op_date = st.date_input("Operation Date", datetime.now())
        surgeon = st.text_input("Surgeon Name", value="Dr. Siravich")
    with col4:
        assistant = st.text_input("Assistant Name")
        op_type = st.text_input("Operation Type")
    
    follow_up = st.selectbox("Follow-up Period", ["Pre-op", "2 week", "3 mo", "6 mo", "12 mo", "24 mo"])

    # 3. Clinical Scores
    st.markdown("#### Clinical Scores")
    pain_score = st.slider("VAS Pain Score (0-10)", 0, 10, 5)
    
    odi_scores = []

    if proc_type == "TL Spine Procedure":
        st.markdown("---")
        
        # Header with Language Switcher
        col_header, col_lang = st.columns([4, 1])
        with col_header:
            st.markdown("### ODI (Oswestry Disability Index)")
        with col_lang:
            odi_lang = st.radio("Language", ["TH", "EN"], horizontal=True, label_visibility="collapsed")
        
        if odi_lang == "TH":
            odi_data = odi_content.ODI_THAI
        else:
            odi_data = odi_content.ODI_EN
        
        # Single Column Layout
        for i, item in enumerate(odi_data):
            st.markdown(f"**{item['question']}**")
            selected_option = st.selectbox(
                "Select option",
                item['options'],
                key=f"odi_q_{i+1}_{odi_lang}",
                label_visibility="collapsed"
            )
            score = item['options'].index(selected_option)
            odi_scores.append(score)
            st.markdown("---")
        
        # Unpack scores for DB saving
        odi_q1, odi_q2, odi_q3, odi_q4, odi_q5, odi_q6, odi_q7, odi_q8, odi_q9, odi_q10 = odi_scores

    else: # C Spine (NDI)
        st.markdown("---")
        
        # Header with Language Switcher
        col_header, col_lang = st.columns([4, 1])
        with col_header:
            st.markdown("### NDI (Neck Disability Index)")
        with col_lang:
            ndi_lang = st.radio("Language", ["TH", "EN"], horizontal=True, label_visibility="collapsed", key="ndi_lang")
        
        if ndi_lang == "TH":
            ndi_data = odi_content.NDI_THAI
        else:
            ndi_data = odi_content.NDI_EN

        # Single Column Layout
        for i, item in enumerate(ndi_data):
            st.markdown(f"**{item['question']}**")
            selected_option = st.selectbox(
                "Select option",
                item['options'],
                key=f"ndi_q_{i+1}_{ndi_lang}",
                label_visibility="collapsed"
            )
            score = item['options'].index(selected_option)
            odi_scores.append(score)
            st.markdown("---")
        
        # Unpack scores for DB saving (reusing ODI columns as requested)
        odi_q1, odi_q2, odi_q3, odi_q4, odi_q5, odi_q6, odi_q7, odi_q8, odi_q9, odi_q10 = odi_scores
    
    st.markdown("---")
    
    # Header with Language Switcher
    col_header_eq, col_lang_eq = st.columns([4, 1])
    with col_header_eq:
        st.markdown("##### EQ-5D-5L")
    with col_lang_eq:
        eq_lang = st.radio("Language", ["TH", "EN"], horizontal=True, label_visibility="collapsed", key="eq_lang")

    if eq_lang == "TH":
        eq_data = odi_content.EQ5D_THAI
    else:
        eq_data = odi_content.EQ5D_EN
        
    eq_scores = []
    
    # Render Questions
    for i, item in enumerate(eq_data):
        st.markdown(f"**{item['question']}**")
        selected_option = st.selectbox(
            "Select option",
            item['options'],
            key=f"eq_q_{i+1}_{eq_lang}",
            label_visibility="collapsed"
        )
        # Extract score from string "1 - Text" -> 1
        score = int(selected_option.split(" - ")[0])
        eq_scores.append(score)
        st.markdown("---")
        
    # Unpack scores
    eq1, eq2, eq3, eq4, eq5 = eq_scores
    
    st.markdown("""
    - เราอยากทราบว่าสุขภาพของท่านเป็นอย่างไรในวันนี้
    - สเกลวัดสุขภาพนี้มีตัวเลขตั้งแต่ 0-100
    - 100 หมายถึงสุขภาพดีที่สุด ตามความคิดของท่าน
    - 0 หมายถึง สุขภาพแย่ที่สุดตามความคิดของท่าน
    - โปรดเลือกตัวเลขบนสเกลเพื่อระบุว่าสุขภาพของท่านเป็นอย่างไรในวันนี้
    """)
    health_status = st.slider("EQ-VAS Health Status (0-100)", 0, 100, 80)
    
    satisfaction = None
    if follow_up != "Pre-op":
        st.markdown("---")
        st.markdown("##### Satisfaction Score (PREM)")
        satisfaction = st.slider("Score (0-10)", 0, 10, 8)
    
    note = st.text_area("Notes")

    # Form Actions
    submitted = st.button("Save Visit", use_container_width=True, type="primary")
        
    if submitted:
        if not hn:
            st.error("Please enter an HN.")
        else:
            # Calculate Scores
            odi_scores = [odi_q1, odi_q2, odi_q3, odi_q4, odi_q5, odi_q6, odi_q7, odi_q8, odi_q9, odi_q10]
            odi_percent = calculate_odi(odi_scores)
            eq_score = calc.calculate_eq5d_score(eq1, eq2, eq3, eq4, eq5)
            
            # Prepare Data Dict
            visit_data = {
                "patient_id": hn, # Renamed from hn
                "visit_date": str(visit_date),
                "gender": gender,
                "age": age,
                "operation_date": str(op_date),
                "surgeon": surgeon,
                "assistant": assistant,
                "operation_type": op_type,
                "procedure_type": proc_type,
                "follow_up_period": follow_up,
                "vas_score": pain_score, # Renamed from pain_score
                "odi_q1": odi_q1, "odi_q2": odi_q2, "odi_q3": odi_q3, "odi_q4": odi_q4, "odi_q5": odi_q5,
                "odi_q6": odi_q6, "odi_q7": odi_q7, "odi_q8": odi_q8, "odi_q9": odi_q9, "odi_q10": odi_q10,
                "odi_score": odi_percent, # Renamed from odi_score_percent
                "eq5d_1": eq1, "eq5d_2": eq2, "eq5d_3": eq3, "eq5d_4": eq4, "eq5d_5": eq5,
                "eq5d_score": eq_score,
                "health_status": health_status,
                "satisfaction_score": satisfaction,
                "note": note
            }
            
            db.add_patient(visit_data)
            st.session_state.submitted = True
            st.rerun()

# --- Footer ---
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: blue;
        color: white;
        text-align: center;
        padding: 10px;
        z-index: 999;
    }
    </style>
    <div class="footer">
        <p>Copyright © 2025 Dr. BRIGHT SIRAVICH</p>
    </div>
    """,
    unsafe_allow_html=True
)

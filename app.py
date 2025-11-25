import streamlit as st
import pandas as pd
import plotly.express as px
import database as db
from datetime import datetime
import questionnaires as q
import importlib

# --- Page Configuration ---
st.set_page_config(
    page_title="BJC ESS Registry Dashboard",
    # page_icon="🏥", # Removed emoji
    layout="wide"
)

# --- Helper Functions for Calculations ---

def calculate_odi(scores):
    """
    Calculates the Oswestry Disability Index (ODI) score.
    Formula: (Sum of scores / (Number of questions answered * 5)) * 100
    Each question is scored 0-5.
    """
    # Filter out None values (unanswered questions) if any
    valid_scores = [s for s in scores if s is not None]
    
    if not valid_scores:
        return 0.0
        
    total_score = sum(valid_scores)
    max_possible_score = len(valid_scores) * 5
    
    if max_possible_score == 0:
        return 0.0
        
    return (total_score / max_possible_score) * 100

def calculate_eq5d_index(dims):
    """
    Calculates EQ-5D-5L Index Score.
    NOTE: This is a placeholder. The actual calculation requires a specific 
    'Value Set' (coefficients) for the Thai population.
    
    Your research team can update the logic below with the official Thai value set coefficients.
    For now, we will return a simple sum-based placeholder or 0.
    """
    # TODO: REPLACE THIS WITH OFFICIAL THAI VALUE SET CALCULATION
    # Example structure: 1 - (constant + coef_mobility + coef_selfcare + ...)
    return 0.0 

# --- Main Application ---

st.title("BJC ESS Registry Dashboard")

# Initialize session state for Patient tab navigation
if 'patient_view' not in st.session_state:
    st.session_state.patient_view = 'list' # 'list' or 'add'

# Create Tabs
tab_dashboard, tab_patient = st.tabs(["Dashboard", "Patient"])

# --- TAB 1: DASHBOARD ---
with tab_dashboard:
    # Load Data
    df = db.get_all_visits()

    if df.empty:
        st.info("No data found. Please add a patient visit in the Patient tab.")
    else:
        # 1. Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Patients", df['hn'].nunique())
        m2.metric("Total Visits", len(df))
        
        # Calculate Avg Pain Improvement (Pre-op vs Last Follow-up)
        # This is a simplified metric for the dashboard card
        pre_op_pain = df[df['follow_up_period'] == 'Pre-op']['pain_score'].mean()
        if pd.isna(pre_op_pain): pre_op_pain = 0
        m3.metric("Avg Pre-op Pain", f"{pre_op_pain:.1f}")
        
        # 2. Charts
        st.markdown("### Analytics")
        c1, c2 = st.columns(2)
        
        with c1:
            # Pain Score by Follow-up Period
            # We want to order the periods logically
            period_order = ["Pre-op", "2 week", "3 mo", "6 mo", "12 mo", "24 mo"]
            df['follow_up_period'] = pd.Categorical(df['follow_up_period'], categories=period_order, ordered=True)
            
            avg_pain = df.groupby('follow_up_period', observed=True)['pain_score'].mean().reset_index()
            fig_pain = px.bar(avg_pain, x='follow_up_period', y='pain_score', 
                              title="Average Pain Score by Follow-up",
                              color='pain_score', color_continuous_scale='RdYlGn_r')
            st.plotly_chart(fig_pain, use_container_width=True)
            
        with c2:
            # ODI Score Distribution
            fig_odi = px.box(df, x='follow_up_period', y='odi_score_percent',
                             title="ODI Score Distribution by Follow-up",
                             color='follow_up_period')
            st.plotly_chart(fig_odi, use_container_width=True)

# --- TAB 2: PATIENT ---
with tab_patient:
    
    # View 1: Patient List
    if st.session_state.patient_view == 'list':
        col_header, col_add_btn = st.columns([4, 1])
        with col_header:
            st.markdown("### Patient Data")
        with col_add_btn:
            if st.button("Add New Patient Visit", use_container_width=True):
                st.session_state.patient_view = 'add'
                st.rerun()
        
        # Load Data (Refresh)
        df = db.get_all_visits()
        
        if df.empty:
            st.info("No patients found.")
        else:
            # Filters
            filter_hn = st.text_input("Search by HN")
            if filter_hn:
                df_display = df[df['hn'].str.contains(filter_hn, case=False)]
            else:
                df_display = df
                
            st.dataframe(df_display, use_container_width=True)
            
            # Actions (Export & Delete)
            st.markdown("---")
            col_actions1, col_actions2 = st.columns([1, 4])
            
            with col_actions1:
                # CSV Export
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download CSV",
                    csv,
                    "patient_data.csv",
                    "text/csv",
                    key='download-csv'
                )
                
            with col_actions2:
                # Delete Record
                with st.expander("Delete Record"):
                    del_id = st.number_input("Enter ID to delete", min_value=1, step=1)
                    if st.button("Delete Visit"):
                        db.delete_visit(del_id)
                        st.warning(f"Record ID {del_id} deleted. Please refresh.")
                        st.rerun()

    # View 2: Add New Patient Visit Form
    elif st.session_state.patient_view == 'add':
        
        # Header Row with Back Button and Import
        col_title, col_import, col_back = st.columns([4, 2, 1])
        with col_title:
            st.markdown("### Add New Patient Visit")
        
        with col_import:
            with st.expander("Import Data"):
                # Template Download
                template_data = {
                    "hn": ["ExampleHN123"],
                    "visit_date": [str(datetime.now().date())],
                    "visit_time": ["09:00:00"],
                    "gender": ["Male"],
                    "age": [45],
                    "operation_date": [str(datetime.now().date())],
                    "surgeon": ["Dr. Siravich"],
                    "assistant": ["Dr. Assistant"],
                    "operation_type": ["TLIF"],
                    "procedure_type": ["TL Spine Procedure"],
                    "follow_up_period": ["Pre-op"],
                    "pain_score": [5],
                    "odi_q1": [0], "odi_q2": [0], "odi_q3": [0], "odi_q4": [0], "odi_q5": [0],
                    "odi_q6": [0], "odi_q7": [0], "odi_q8": [0], "odi_q9": [0], "odi_q10": [0],
                    "eq5d_1": [1], "eq5d_2": [1], "eq5d_3": [1], "eq5d_4": [1], "eq5d_5": [1],
                    "health_status": [80],
                    "satisfaction_score": [8],
                    "note": ["Imported record"]
                }
                df_template = pd.DataFrame(template_data)
                csv_template = df_template.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="Download Template CSV",
                    data=csv_template,
                    file_name="patient_import_template.csv",
                    mime="text/csv",
                    help="Use this template to format your data for upload."
                )

                st.markdown("---")

                uploaded_file = st.file_uploader("Upload CSV/XLSX", type=['csv', 'xlsx'])
                if uploaded_file:
                    if st.button("Process Import"):
                        try:
                            if uploaded_file.name.endswith('.csv'):
                                df_import = pd.read_csv(uploaded_file)
                            else:
                                df_import = pd.read_excel(uploaded_file)
                            
                            # Normalize columns: lowercase and strip whitespace
                            df_import.columns = df_import.columns.str.strip().str.lower()

                            # Basic validation
                            if 'hn' not in df_import.columns:
                                st.error("File must contain 'hn' column.")
                            else:
                                success_count = 0
                                for index, row in df_import.iterrows():
                                    # Convert row to dict and clean up
                                    visit_data = row.to_dict()
                                    
                                    # Handle NaN/None
                                    for key, value in visit_data.items():
                                        if pd.isna(value):
                                            visit_data[key] = None
                                        else:
                                            # Convert dates/times to string if needed
                                            if isinstance(value, (pd.Timestamp, datetime)):
                                                visit_data[key] = str(value)

                                    db.add_visit(visit_data)
                                    success_count += 1
                                st.success(f"Imported {success_count} records!")
                                st.session_state.patient_view = 'list'
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error importing file: {e}")

        with col_back:
            if st.button("Back", use_container_width=True):
                st.session_state.patient_view = 'list'
                st.rerun()
        
        # Procedure Type Selector (Outside form to enable dynamic updates)
        st.markdown("#### Procedure Info")
        proc_type = st.radio("Procedure Type", ["TL Spine Procedure", "C Spine Procedure"], horizontal=True)
            
        with st.form("visit_form"):
            # 1. Patient Info
            st.markdown("#### Patient Details")
            hn = st.text_input("HN (Hospital Number)")
            
            col1, col2 = st.columns(2)
            with col1:
                gender = st.selectbox("Gender", ["Male", "Female"])
                age = st.number_input("Age", min_value=0, max_value=120, step=1)
            with col2:
                visit_date = st.date_input("Visit Date", datetime.now())
                visit_time = st.time_input("Visit Time", datetime.now())

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
            
            # Dynamic Header and Questions based on Procedure Type
            import odi_content as odi_content
            odi_scores = []

            if proc_type == "TL Spine Procedure":
                st.markdown("---")
                
                # Header with Language Switcher
                col_header, col_lang = st.columns([4, 1])
                with col_header:
                    st.markdown("### ODI (Oswestry Disability Index)")
                with col_lang:
                    # Simplified Language Switcher
                    odi_lang = st.radio("Language", ["TH", "EN"], horizontal=True, label_visibility="collapsed")
                
                
                if odi_lang == "TH":
                    odi_data = odi_content.ODI_THAI
                else:
                    odi_data = odi_content.ODI_EN
                
                # st.write(f"Debug: Lang={odi_lang}")
                # st.write(f"Debug: Q1={odi_data[0]['question']}")

                # Single Column Layout
                for i, item in enumerate(odi_data):
                    st.markdown(f"**{item['question']}**")
                    # Create a unique key for each question's dropdown based on language
                    selected_option = st.selectbox(
                        "Select option",
                        item['options'],
                        key=f"odi_q_{i+1}_{odi_lang}",
                        label_visibility="collapsed"
                    )
                    # The score is the index of the selected option (0-5)
                    score = item['options'].index(selected_option)
                    odi_scores.append(score)
                    # Removed "Score: X" display
                    st.markdown("---")
                
                # Unpack scores for DB saving
                odi_q1, odi_q2, odi_q3, odi_q4, odi_q5, odi_q6, odi_q7, odi_q8, odi_q9, odi_q10 = odi_scores

            else: # C Spine (NDI)
                st.markdown("##### NDI (Neck Disability Index)")
                st.caption("0=No pain, 5=Worst pain")
                q_labels = [
                    "Q1: Pain Intensity", "Q2: Personal Care", "Q3: Lifting", "Q4: Reading", "Q5: Headaches",
                    "Q6: Concentration", "Q7: Work", "Q8: Driving", "Q9: Sleeping", "Q10: Recreation"
                ]
                
                # Group NDI questions
                ndi_cols = st.columns(2)
                with ndi_cols[0]:
                    odi_q1 = st.selectbox(q_labels[0], range(6), index=0)
                    odi_q2 = st.selectbox(q_labels[1], range(6), index=0)
                    odi_q3 = st.selectbox(q_labels[2], range(6), index=0)
                    odi_q4 = st.selectbox(q_labels[3], range(6), index=0)
                    odi_q5 = st.selectbox(q_labels[4], range(6), index=0)
                with ndi_cols[1]:
                    odi_q6 = st.selectbox(q_labels[5], range(6), index=0)
                    odi_q7 = st.selectbox(q_labels[6], range(6), index=0)
                    odi_q8 = st.selectbox(q_labels[7], range(6), index=0)
                    odi_q9 = st.selectbox(q_labels[8], range(6), index=0)
                    odi_q10 = st.selectbox(q_labels[9], range(6), index=0)
            
            st.markdown("##### EQ-5D-5L")
            eq_cols = st.columns(5)
            with eq_cols[0]: eq1 = st.selectbox("Mobility", [1,2,3,4,5])
            with eq_cols[1]: eq2 = st.selectbox("Self-care", [1,2,3,4,5])
            with eq_cols[2]: eq3 = st.selectbox("Usual Activities", [1,2,3,4,5])
            with eq_cols[3]: eq4 = st.selectbox("Pain/Discomfort", [1,2,3,4,5])
            with eq_cols[4]: eq5 = st.selectbox("Anxiety/Depression", [1,2,3,4,5])
            
            health_status = st.slider("EQ-VAS Health Status (0-100)", 0, 100, 80)
            satisfaction = st.slider("Satisfaction Score (PREM)", 0, 10, 8)
            
            note = st.text_area("Notes")

            # Form Actions
            submitted = st.form_submit_button("Save Visit", use_container_width=True)
            
        if submitted:
            if not hn:
                st.error("Please enter an HN.")
            else:
                # Calculate Scores
                odi_scores = [odi_q1, odi_q2, odi_q3, odi_q4, odi_q5, odi_q6, odi_q7, odi_q8, odi_q9, odi_q10]
                odi_percent = calculate_odi(odi_scores)
                eq_dims = [eq1, eq2, eq3, eq4, eq5]
                eq_score = calculate_eq5d_index(eq_dims)
                
                # Prepare Data Dict
                visit_data = {
                    "hn": hn,
                    "visit_date": str(visit_date),
                    "visit_time": str(visit_time),
                    "gender": gender,
                    "age": age,
                    "operation_date": str(op_date),
                    "surgeon": surgeon,
                    "assistant": assistant,
                    "operation_type": op_type,
                    "procedure_type": proc_type,
                    "follow_up_period": follow_up,
                    "pain_score": pain_score,
                    "odi_q1": odi_q1, "odi_q2": odi_q2, "odi_q3": odi_q3, "odi_q4": odi_q4, "odi_q5": odi_q5,
                    "odi_q6": odi_q6, "odi_q7": odi_q7, "odi_q8": odi_q8, "odi_q9": odi_q9, "odi_q10": odi_q10,
                    "odi_score_percent": odi_percent,
                    "eq5d_1": eq1, "eq5d_2": eq2, "eq5d_3": eq3, "eq5d_4": eq4, "eq5d_5": eq5,
                    "eq5d_score": eq_score,
                    "health_status": health_status,
                    "satisfaction_score": satisfaction,
                    "note": note
                }
                
                db.add_visit(visit_data)
                st.success(f"Visit saved for HN {hn}!")
                st.session_state.patient_view = 'list'
                st.rerun()

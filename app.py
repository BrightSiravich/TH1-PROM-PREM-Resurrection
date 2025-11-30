import streamlit as st
import pandas as pd
import plotly.express as px
import database as db
from datetime import datetime
import questionnaires as q
import importlib
import calculations as calc

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
    
    # Constraint: If fewer than 7 sections answered, score is invalid
    if len(valid_scores) < 7:
        return None
        
    total_score = sum(valid_scores)
    max_possible_score = len(valid_scores) * 5
    
    if max_possible_score == 0:
        return 0.0
        
    return (total_score / max_possible_score) * 100 

@st.cache_data
def convert_df(df):
    """
    Converts a DataFrame to CSV with utf-8-sig encoding.
    Cached to prevent re-computation and ensure stable download object.
    """
    return df.to_csv(index=False).encode('utf-8-sig')

def render_analytics(df, title="Overall Analytics"):
    """
    Renders the analytics dashboard section given a dataframe.
    """
    # 1. Calculate Metrics
    
    # Filter for patients with Pre-op data
    pre_op_df = df[df['follow_up_period'] == 'Pre-op'][['hn', 'pain_score', 'odi_score_percent', 'eq5d_score', 'health_status']]
    
    # Filter for patients with Follow-up data (excluding Pre-op)
    follow_up_df = df[df['follow_up_period'] != 'Pre-op'][['hn', 'pain_score', 'odi_score_percent', 'eq5d_score', 'health_status', 'satisfaction_score']]
    
    patients_with_pre_op = pre_op_df['hn'].unique()
    
    # Initialize counters
    pain_improved_count = 0
    pain_total_eval = 0
    odi_improved_count = 0
    odi_total_eval = 0
    eq5d_improved_count = 0
    eq5d_total_eval = 0
    vas_improved_count = 0
    vas_total_eval = 0
    
    for hn in patients_with_pre_op:
        patient_pre = pre_op_df[pre_op_df['hn'] == hn].iloc[0]
        patient_post = follow_up_df[follow_up_df['hn'] == hn]
        
        if patient_post.empty:
            continue
            
        # Pain Improvement (Decrease)
        if pd.notna(patient_pre['pain_score']):
            valid_post = patient_post['pain_score'].dropna()
            if not valid_post.empty:
                pain_total_eval += 1
                if (valid_post < patient_pre['pain_score']).any():
                    pain_improved_count += 1
                    
        # ODI Improvement (Decrease)
        if pd.notna(patient_pre['odi_score_percent']):
            valid_post = patient_post['odi_score_percent'].dropna()
            if not valid_post.empty:
                odi_total_eval += 1
                if (valid_post < patient_pre['odi_score_percent']).any():
                    odi_improved_count += 1

        # EQ5D Improvement (Increase)
        if pd.notna(patient_pre['eq5d_score']):
            valid_post = patient_post['eq5d_score'].dropna()
            if not valid_post.empty:
                eq5d_total_eval += 1
                if (valid_post > patient_pre['eq5d_score']).any():
                    eq5d_improved_count += 1

        # VAS Improvement (Increase)
        if pd.notna(patient_pre['health_status']):
            valid_post = patient_post['health_status'].dropna()
            if not valid_post.empty:
                vas_total_eval += 1
                if (valid_post > patient_pre['health_status']).any():
                    vas_improved_count += 1
    
    # Calculate Percentages
    pct_pain = (pain_improved_count / pain_total_eval * 100) if pain_total_eval > 0 else 0.0
    pct_odi = (odi_improved_count / odi_total_eval * 100) if odi_total_eval > 0 else 0.0
    pct_eq5d = (eq5d_improved_count / eq5d_total_eval * 100) if eq5d_total_eval > 0 else 0.0
    pct_vas = (vas_improved_count / vas_total_eval * 100) if vas_total_eval > 0 else 0.0
    
    # Avg Satisfaction (All follow-up visits)
    avg_sat = follow_up_df['satisfaction_score'].mean()
    if pd.isna(avg_sat): avg_sat = 0.0

    # Display Metrics
    # Row 1
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Patients", df['hn'].nunique())
    m2.metric("Total Visits", len(df))
    m3.metric("Avg Satisfaction", f"{avg_sat:.1f}/10")
    
    # Row 2
    m4, m5, m6, m7 = st.columns(4)
    m4.metric("% Pain Improve", f"{pct_pain:.1f}%")
    m5.metric("% ODI Improve", f"{pct_odi:.1f}%")
    m6.metric("% EQ5D5L Improve", f"{pct_eq5d:.1f}%")
    m7.metric("% EQVAS Improve", f"{pct_vas:.1f}%")
    
    # 2. Charts
    st.markdown(f"### {title}")
    
    # Ensure categorical order for all charts
    period_order = ["Pre-op", "2 week", "3 mo", "6 mo", "12 mo", "24 mo"]
    df = df.copy() # Avoid SettingWithCopyWarning on the original df
    df['follow_up_period'] = pd.Categorical(df['follow_up_period'], categories=period_order, ordered=True)

    # Row 1: Pain & ODI
    r1c1, r1c2 = st.columns(2)
    
    with r1c1:
        # Pain Score Distribution (Box Plot)
        fig_pain = px.box(df, x='follow_up_period', y='pain_score', 
                          title="Pain Score Distribution by Follow-up",
                          color='follow_up_period',
                          category_orders={"follow_up_period": period_order})
        st.plotly_chart(fig_pain, use_container_width=True)
        
    with r1c2:
        # ODI Score Distribution
        fig_odi = px.box(df, x='follow_up_period', y='odi_score_percent',
                         title="ODI Score Distribution by Follow-up",
                         color='follow_up_period',
                         category_orders={"follow_up_period": period_order})
        st.plotly_chart(fig_odi, use_container_width=True)

    # Row 2: EQ-5D & Health VAS
    r2c1, r2c2 = st.columns(2)
    
    with r2c1:
        # EQ-5D-5L Distribution
        fig_eq = px.box(df, x='follow_up_period', y='eq5d_score',
                        title="EQ-5D-5L Score Distribution by Follow-up",
                        color='follow_up_period',
                        category_orders={"follow_up_period": period_order})
        st.plotly_chart(fig_eq, use_container_width=True)
        
    with r2c2:
        # EQ-VAS Health Status Distribution
        fig_vas = px.box(df, x='follow_up_period', y='health_status',
                         title="EQ-VAS Health Status Distribution by Follow-up",
                         color='follow_up_period',
                         category_orders={"follow_up_period": period_order})
        st.plotly_chart(fig_vas, use_container_width=True)

    # Row 3: Satisfaction
    r3c1, r3c2 = st.columns(2)
    with r3c1:
        # Satisfaction Score Distribution
        fig_sat = px.box(df, x='follow_up_period', y='satisfaction_score',
                         title="Satisfaction Score Distribution by Follow-up",
                         color='follow_up_period',
                         category_orders={"follow_up_period": period_order})
        st.plotly_chart(fig_sat, use_container_width=True)

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
        render_analytics(df, "Overall Analytics")

# --- TAB 2: PATIENT ---
with tab_patient:
    
    # View 1: Patient List
    if st.session_state.patient_view == 'list':
        
        # Initialize delete mode state
        if 'delete_mode' not in st.session_state:
            st.session_state.delete_mode = False
            
        col_header, col_search_btn, col_delete_btn, col_add_btn = st.columns([3, 1, 1, 1])
        with col_header:
            st.markdown("### Patient Data")
            
        with col_search_btn:
             if st.button("Search", use_container_width=True):
                st.session_state.patient_view = 'search'
                st.rerun()

        with col_delete_btn:
            # Toggle Delete Mode
            btn_label = "Cancel Delete" if st.session_state.delete_mode else "Delete"
            btn_type = "secondary" if st.session_state.delete_mode else "secondary"
            if st.button(btn_label, use_container_width=True, type=btn_type):
                st.session_state.delete_mode = not st.session_state.delete_mode
                st.rerun()
                
        with col_add_btn:
            if st.button("Add", use_container_width=True):
                st.session_state.patient_view = 'add'
                st.rerun()
        
        # Load Data (Refresh)
        df = db.get_all_visits()
        
        if df.empty:
            st.info("No patients found.")
        else:
            # Filters - Removed simple search as requested
            df_display = df
                
            # Remove visit_time from display if it exists
            if 'visit_time' in df_display.columns:
                df_display = df_display.drop(columns=['visit_time'])

            # --- Display Logic ---
            if st.session_state.delete_mode:
                # Select All Checkbox
                select_all = st.checkbox("Select All Rows")

                # Add a selection column
                df_display_editor = df_display.copy()
                df_display_editor.insert(0, "Select", select_all)
                
                # Use data_editor for selection
                edited_df = st.data_editor(
                    df_display_editor,
                    hide_index=True,
                    column_config={"Select": st.column_config.CheckboxColumn(required=True)},
                    disabled=df_display.columns,
                    use_container_width=True,
                    key="data_editor"
                )
                
                # Identify selected rows
                selected_rows = edited_df[edited_df.Select]
                
                if not selected_rows.empty:
                    st.error(f"Selected {len(selected_rows)} record(s) for deletion.")
                    
                    if st.button("Confirm Delete", type="primary"):
                        # Delete logic
                        for index, row in selected_rows.iterrows():
                            db.delete_visit(row['id'])
                        
                        st.success(f"Deleted {len(selected_rows)} records.")
                        st.session_state.delete_mode = False
                        st.rerun()
            else:
                # Normal Display
                st.dataframe(df_display, use_container_width=True)
            
            # Actions (Export) - Delete is now handled above
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

    # View 2: Add New Patient Visit Form
    elif st.session_state.patient_view == 'add':
        
        # Header Row with Back Button and Import
        col_title, col_import, col_back = st.columns([4, 2, 1])
        with col_title:
            st.markdown("### Add New Patient Visit")
        
        with col_import:
            with st.expander("Import Data"):
                # Template Download
                # Template Download
                with open("patient_import_template.csv", "rb") as f:
                    st.download_button(
                        label="Download Template CSV",
                        data=f,
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
                                    encodings = ['utf-8-sig', 'utf-8', 'cp874', 'tis-620']
                                    for encoding in encodings:
                                        try:
                                            uploaded_file.seek(0)
                                            df_import = pd.read_csv(uploaded_file, encoding=encoding)
                                            break
                                        except UnicodeDecodeError:
                                            continue
                                    else:
                                        raise ValueError("Could not determine file encoding")
                            else:
                                df_import = pd.read_excel(uploaded_file)
                            
                            # Normalize columns: lowercase and strip whitespace
                            df_import.columns = df_import.columns.str.strip().str.lower()
                            
                            # Normalize Gender (Thai -> English)
                            if 'gender' in df_import.columns:
                                df_import['gender'] = df_import['gender'].replace({'ชาย': 'Male', 'หญิง': 'Female'})

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

                                    # Auto-calculate ODI Score
                                    odi_scores = []
                                    for i in range(1, 11):
                                        q_key = f'odi_q{i}'
                                        # Ensure key exists and is numeric
                                        if q_key in visit_data and visit_data[q_key] is not None:
                                            try:
                                                odi_scores.append(float(visit_data[q_key]))
                                            except (ValueError, TypeError):
                                                pass # Skip invalid values
                                    
                                    visit_data['odi_score_percent'] = calculate_odi(odi_scores)

                                    # Auto-calculate EQ-5D Score
                                    try:
                                        eq_dims = []
                                        for i in range(1, 6):
                                            key = f'eq5d_{i}'
                                            if key in visit_data and visit_data[key] is not None:
                                                eq_dims.append(int(float(visit_data[key]))) # Handle float inputs like 1.0
                                            else:
                                                eq_dims.append(None)
                                        
                                        # Only calculate if all 5 dims are present
                                        if all(d is not None for d in eq_dims):
                                            visit_data['eq5d_score'] = calc.calculate_eq5d_score(*eq_dims)
                                    except (ValueError, TypeError):
                                        pass # Skip if invalid data

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
        
        # Language Switcher moved to specific sections

            
        # Form removed to allow dynamic updates
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
                # Create a unique key for each question's dropdown based on language
                selected_option = st.selectbox(
                    "Select option",
                    item['options'],
                    key=f"ndi_q_{i+1}_{ndi_lang}",
                    label_visibility="collapsed"
                )
                # The score is the index of the selected option (0-5)
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
        submitted = st.button("Save Visit", use_container_width=True)
            
        if submitted:
            if not hn:
                st.error("Please enter an HN.")
            else:
                # Calculate Scores
                odi_scores = [odi_q1, odi_q2, odi_q3, odi_q4, odi_q5, odi_q6, odi_q7, odi_q8, odi_q9, odi_q10]
                odi_percent = calculate_odi(odi_scores)
                # eq_dims = [eq1, eq2, eq3, eq4, eq5]
                eq_score = calc.calculate_eq5d_score(eq1, eq2, eq3, eq4, eq5)
                
                # Prepare Data Dict
                visit_data = {
                    "hn": hn,
                    "visit_date": str(visit_date),
                    # "visit_time": str(visit_time), # Removed
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

    # View 3: Advanced Search
    elif st.session_state.patient_view == 'search':
        col_title, col_back = st.columns([5, 1])
        with col_title:
            st.markdown("### Advanced Search")
        with col_back:
            if st.button("Back", use_container_width=True):
                st.session_state.patient_view = 'list'
                st.rerun()
        
        # Initialize search state
        if 'search_results' not in st.session_state:
            st.session_state.search_results = None
        if 'search_performed' not in st.session_state:
            st.session_state.search_performed = False
        
        # Search Form
        with st.form("search_form"):
            st.markdown("#### Search Criteria")
            
            # Row 1: Basic Info
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                s_hn = st.text_input("HN")
            with c2:
                s_gender = st.multiselect("Gender", ["Male", "Female"])
            with c3:
                s_age_min, s_age_max = st.slider("Age Range", 0, 120, (0, 120))
            with c4:
                s_follow_up = st.multiselect("Follow-up Period", ["Pre-op", "2 week", "3 mo", "6 mo", "12 mo", "24 mo"])

            # Row 2: Dates
            c5, c6 = st.columns(2)
            with c5:
                s_visit_date_start = st.date_input("Visit Date (Start)", value=None)
                s_visit_date_end = st.date_input("Visit Date (End)", value=None)
            with c6:
                s_op_date_start = st.date_input("Operation Date (Start)", value=None)
                s_op_date_end = st.date_input("Operation Date (End)", value=None)

            # Row 3: Procedure Info
            c7, c8, c9 = st.columns(3)
            with c7:
                s_surgeon = st.text_input("Surgeon")
            with c8:
                s_assistant = st.text_input("Assistant")
            with c9:
                s_op_type = st.text_input("Operation Type")

            st.markdown("#### Scores")
            # Row 4: Scores
            c10, c11 = st.columns(2)
            with c10:
                s_pain_min, s_pain_max = st.slider("Pain VAS Score (0-10)", 0, 10, (0, 10))
            with c11:
                s_odi_min, s_odi_max = st.slider("ODI Score % (0-100)", 0.0, 100.0, (0.0, 100.0))
            
            c12, c13, c14 = st.columns(3)
            with c12:
                s_eq_score_min = st.number_input("Min EQ5D Score", value=-1.0, step=0.1)
                s_eq_score_max = st.number_input("Max EQ5D Score", value=1.0, step=0.1)
            with c13:
                s_health_min, s_health_max = st.slider("EQ-VAS Health Status (0-100)", 0, 100, (0, 100))
            with c14:
                s_sat_min, s_sat_max = st.slider("Satisfaction Score (0-10)", 0, 10, (0, 10))

            submitted_search = st.form_submit_button("Submit Search", type="primary")

        if submitted_search:
            st.session_state.show_custom_analytics = False
            df_search = db.get_all_visits()
            
            if df_search.empty:
                st.warning("No data to search.")
                st.session_state.search_performed = False
                st.session_state.search_results = None
            else:
                # Apply Filters
                # Apply Filters
                if s_hn:
                    # Ensure HN is string and strip whitespace for comparison
                    df_search = df_search[df_search['hn'].astype(str).str.contains(s_hn.strip(), case=False, na=False)]
                if s_gender:
                    df_search = df_search[df_search['gender'].isin(s_gender)]
                
                if s_age_min > 0 or s_age_max < 120:
                    df_search = df_search[(df_search['age'] >= s_age_min) & (df_search['age'] <= s_age_max)]
                
                if s_follow_up:
                    df_search = df_search[df_search['follow_up_period'].isin(s_follow_up)]
                
                # Date Filters
                if s_visit_date_start:
                    df_search = df_search[pd.to_datetime(df_search['visit_date'], errors='coerce').dt.date >= s_visit_date_start]
                if s_visit_date_end:
                    df_search = df_search[pd.to_datetime(df_search['visit_date'], errors='coerce').dt.date <= s_visit_date_end]
                    
                if s_op_date_start:
                    df_search = df_search[pd.to_datetime(df_search['operation_date'], errors='coerce').dt.date >= s_op_date_start]
                if s_op_date_end:
                    df_search = df_search[pd.to_datetime(df_search['operation_date'], errors='coerce').dt.date <= s_op_date_end]

                if s_surgeon:
                    df_search = df_search[df_search['surgeon'].str.contains(s_surgeon, case=False, na=False)]
                if s_assistant:
                    df_search = df_search[df_search['assistant'].str.contains(s_assistant, case=False, na=False)]
                if s_op_type:
                    df_search = df_search[df_search['operation_type'].str.contains(s_op_type, case=False, na=False)]

                if s_pain_min > 0 or s_pain_max < 10:
                    df_search = df_search[(df_search['pain_score'] >= s_pain_min) & (df_search['pain_score'] <= s_pain_max)]
                
                if s_odi_min > 0.0 or s_odi_max < 100.0:
                    df_search = df_search[(df_search['odi_score_percent'] >= s_odi_min) & (df_search['odi_score_percent'] <= s_odi_max)]
                
                # EQ5D Score
                # Only filter if user changed defaults (-1.0 to 1.0)
                if s_eq_score_min > -1.0 or s_eq_score_max < 1.0:
                     df_search = df_search[(df_search['eq5d_score'].fillna(-99) >= s_eq_score_min) & (df_search['eq5d_score'].fillna(99) <= s_eq_score_max)]
                
                if s_health_min > 0 or s_health_max < 100:
                    df_search = df_search[(df_search['health_status'] >= s_health_min) & (df_search['health_status'] <= s_health_max)]
                
                # Satisfaction (Handle None for Pre-op)
                # Only filter if range is restricted
                if s_sat_min > 0 or s_sat_max < 10:
                    df_search = df_search[df_search['satisfaction_score'].notna()]
                    df_search = df_search[(df_search['satisfaction_score'] >= s_sat_min) & (df_search['satisfaction_score'] <= s_sat_max)]
                
                st.session_state.search_results = df_search
                st.session_state.search_performed = True

        # Display Results from Session State
        if st.session_state.get('search_performed', False) and st.session_state.search_results is not None:
            df_results = st.session_state.search_results
            st.markdown(f"### Results: {len(df_results)} records found")
            st.dataframe(df_results, use_container_width=True)
            
            st.markdown("---")
            if st.button("Custom Analytics"):
                st.session_state.show_custom_analytics = True
            
            if st.session_state.get('show_custom_analytics', False):
                render_analytics(df_results, "Custom Analytics")

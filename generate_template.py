import pandas as pd
from datetime import datetime

template_data = {
    "hn": ["ExampleHN123"],
    "visit_date": [str(datetime.now().date())],
    # "visit_time": ["09:00:00"], # Removed
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
# Save with utf-8-sig for Excel compatibility
df_template.to_csv("patient_import_template.csv", index=False, encoding='utf-8-sig')
print("Template generated successfully: patient_import_template.csv")

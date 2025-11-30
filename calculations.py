import pandas as pd
import streamlit as st

@st.cache_data
def load_eq5d_data():
    # Load the Excel file. engine='openpyxl' is standard for xlsx.
    # We force 'Profile' to be string to ensure "11111" doesn't become the number 11,111
    try:
        df = pd.read_excel('Thai EQ5D5L Reference Value.xlsx', engine='openpyxl', dtype={'Profile': str})
        return df
    except FileNotFoundError:
        st.error("Error: 'Thai EQ5D5L Reference Value.xlsx' not found.")
        return pd.DataFrame()

def calculate_eq5d_score(mo, sc, ua, pd_score, ad):
    """
    Inputs: Integers 1-5 representing the 5 dimensions.
    Output: Float (Thai Utility Score) or None if not found.
    """
    # 1. Generate the Profile Key as a string
    profile_key = f"{mo}{sc}{ua}{pd_score}{ad}"
    
    # 2. Look up the key
    df = load_eq5d_data()
    
    if df.empty:
        return None

    # Filter the dataframe to find the matching profile
    result = df[df['Profile'] == profile_key]
    
    if not result.empty:
        return float(result['Utility'].iloc[0])
    else:
        return None

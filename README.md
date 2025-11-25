# Hospital PROs & PREMs App

A modern, lightweight application for tracking patient outcomes (VAS, ODI, EQ-5D) built with Python and Streamlit.

## 🚀 How to Run

1.  **Install Dependencies** (First time only):
    Open your terminal and run:
    ```bash
    pip3 install -r requirements.txt
    ```

2.  **Start the App**:
    ```bash
    python3 -m streamlit run app.py
    ```

3.  **Access**:
    The app will open automatically in your web browser at `http://localhost:8501`.

## 📂 Project Structure

*   `app.py`: The main application file containing the dashboard and user interface.
*   `database.py`: Handles all database operations (SQLite).
*   `patients.db`: The local database file (created automatically when you run the app).
*   `requirements.txt`: List of Python libraries required.

## 🛠 Features

*   **Add Visit**: Sidebar form to record new patient data.
*   **Dashboard**: View total patients, visits, and improvement metrics.
*   **Charts**: Visual analysis of Pain Scores and ODI recovery.
*   **Export**: Download your entire database as a CSV file for research.

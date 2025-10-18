# 💸 Expense Management Game 💸

This is a simple personal finance management web application built with Streamlit.

It gamifies the process of managing four accounts (one savings, three credit) by tracking "Health Points" (HP) and "Risk Points" to encourage healthy financial habits.

## Features

-   **Accounts Overview**: See all your balances and account health (HP) at a glance.
-   **Monthly Actions**: Input your monthly income, expenses, and debt payments.
-   **Gamification**:
    -   Account HP drops with high debt and rises with payments.
    -   "Risk Points" increase when using one credit card to pay another.
-   **Visualization**: Tracks your account balances, monthly cash flow, and HP/Risk over time.
-   **Persistence**: Your game state and history are automatically saved to a `finance_history.csv` file.

## How to Run Locally

1.  **Clone the repository** or download the files (`app.py`, `requirements.txt`).
2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install the requirements**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the app**:
    ```bash
    streamlit run app.py
    ```

## Deployment

To deploy on Streamlit Cloud, simply:
1.  Upload this repository (or a new one containing `app.py`, `requirements.txt`, and this `README.md`) to GitHub.
2.  Connect your GitHub account to Streamlit Cloud.
3.  Select the repository and click "Deploy".

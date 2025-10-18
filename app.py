# app.py
# A simple personal finance management "game" built with Streamlit.
# To run:
# 1. Save this file as app.py
# 2. Make sure you have streamlit and pandas:
#    pip install streamlit pandas
# 3. In your terminal, run:
#    streamlit run app.py

import streamlit as st
import pandas as pd
import os
import altair as alt # Used for more flexible charting

# --- Constants ---
HISTORY_FILE = "finance_history.csv"
ACCOUNTS = ["Savings", "Kotak", "IDFC", "Supermoney"]
DEBT_ACCOUNTS = ["Kotak", "IDFC", "Supermoney"]

# --- Utility Functions ---

def get_color_from_value(value, high_is_bad=True, medium_threshold=5000, high_threshold=15000):
    """Returns a color based on a value and thresholds."""
    if high_is_bad:
        if value > high_threshold:
            return "red"
        elif value > medium_threshold:
            return "orange"
        else:
            return "green"
    else: # Low is bad (e.g., Savings)
        if value < medium_threshold:
            return "red"
        elif value < high_threshold:
            return "orange"
        else:
            return "green"

def display_account_card(col, name, balance, hp, is_debt=False):
    """Renders a single account's info card in a Streamlit column."""
    
    # Get settings from session state
    medium_threshold = st.session_state.get('debt_medium', 5000)
    high_threshold = st.session_state.get('debt_high', 15000)

    if is_debt:
        label = f"💳 {name} (Debt)"
        color = get_color_from_value(balance, high_is_bad=True, medium_threshold=medium_threshold, high_threshold=high_threshold)
        delta_color = "inverse" if balance > 0 else "off"
        st.metric(label=label, value=f"₹{balance:,.2f}", delta=f"{hp} HP", delta_color=delta_color)
    else: # Savings Account
        label = f"💰 {name}"
        # For savings, low balance is bad
        color = get_color_from_value(balance, high_is_bad=False, medium_threshold=medium_threshold, high_threshold=high_threshold)
        delta_color = "normal" if balance > high_threshold else "inverse"
        st.metric(label=label, value=f"₹{balance:,.2f}", delta=f"{hp} HP", delta_color=delta_color)

    # Custom colored progress bar
    st.markdown(f"""
    <div style="background: #f0f2f6; border-radius: 5px; height: 10px; margin-top: 5px;">
        <div style="width: {hp}%; background-color: {color}; height: 10px; border-radius: 5px;"></div>
    </div>
    """, unsafe_allow_html=True)


def load_data():
    """Loads history from CSV or returns a new DataFrame."""
    if os.path.exists(HISTORY_FILE):
        try:
            return pd.read_csv(HISTORY_FILE)
        except pd.errors.EmptyDataError:
            return create_empty_history_df()
    else:
        return create_empty_history_df()

def create_empty_history_df():
    """Creates the structure for the history DataFrame."""
    columns = [
        "Month",
        "Savings_Balance", "Kotak_Debt", "IDFC_Debt", "Supermoney_Debt",
        "Savings_HP", "Kotak_HP", "IDFC_HP", "Supermoney_HP",
        "Risk_Points",
        "Total_Payments", "Total_Expenses", "New_Income"
    ]
    return pd.DataFrame(columns=columns)

def save_data():
    """Saves the session state history to CSV."""
    st.session_state.history.to_csv(HISTORY_FILE, index=False)

def initialize_state():
    """
    Initializes the game state.
    Loads from CSV if it exists, otherwise sets defaults.
    """
    if 'initialized' in st.session_state:
        return

    history_df = load_data()

    if history_df.empty:
        # Start a new game
        st.session_state.month = 1
        st.session_state.accounts = {
            "Savings": 50000.0,
            "Kotak": 0.0,
            "IDFC": 0.0,
            "Supermoney": 0.0
        }
        st.session_state.hp = {
            "Savings": 100,
            "Kotak": 100,
            "IDFC": 100,
            "Supermoney": 100
        }
        st.session_state.risk_points = 0
        
        # Save this initial state as Month 0 (start)
        initial_entry = {
            "Month": 0,
            "Savings_Balance": 50000.0, "Kotak_Debt": 0.0, "IDFC_Debt": 0.0, "Supermoney_Debt": 0.0,
            "Savings_HP": 100, "Kotak_HP": 100, "IDFC_HP": 100, "Supermoney_HP": 100,
            "Risk_Points": 0,
            "Total_Payments": 0.0, "Total_Expenses": 0.0, "New_Income": 50000.0
        }
        st.session_state.history = pd.DataFrame([initial_entry])
        save_data()
        
    else:
        # Load the last known state from history
        st.session_state.history = history_df
        last_row = history_df.iloc[-1]
        
        st.session_state.month = int(last_row["Month"]) + 1
        st.session_state.accounts = {
            "Savings": last_row["Savings_Balance"],
            "Kotak": last_row["Kotak_Debt"],
            "IDFC": last_row["IDFC_Debt"],
            "Supermoney": last_row["Supermoney_Debt"]
        }
        st.session_state.hp = {
            "Savings": int(last_row["Savings_HP"]),
            "Kotak": int(last_row["Kotak_HP"]),
            "IDFC": int(last_row["IDFC_HP"]),
            "Supermoney": int(last_row["Supermoney_HP"])
        }
        st.session_state.risk_points = int(last_row["Risk_Points"])

    # Game settings (initialized every time, not saved in CSV for simplicity)
    st.session_state.debt_high = st.sidebar.number_input(
        "High Debt Threshold (₹)", value=15000, min_value=1, step=1000,
        help="Debt above this amount will appear RED and cause high HP loss."
    )
    st.session_state.debt_medium = st.sidebar.number_input(
        "Medium Debt Threshold (₹)", value=5000, min_value=1, step=500,
        help="Debt above this amount will appear ORANGE and cause medium HP loss."
    )
    
    st.session_state.initialized = True


def update_hp_and_risk(payments, card_to_card_amount):
    """Updates HP and Risk Points based on new balances and actions."""
    
    # Get settings
    medium_threshold = st.session_state.debt_medium
    high_threshold = st.session_state.debt_high

    # 1. Update Risk Points
    if card_to_card_amount > 0:
        st.session_state.risk_points += 50 # Flat penalty
        st.warning(f"Using credit to pay credit added 50 Risk Points! Total: {st.session_state.risk_points}")
    else:
        # Risk decay
        st.session_state.risk_points = max(0, st.session_state.risk_points - 10)

    # 2. Update HP for Savings
    savings_balance = st.session_state.accounts["Savings"]
    if savings_balance < medium_threshold:
        st.session_state.hp["Savings"] -= 20
        st.toast("Savings HP dropped! Balance is critically low.", icon="😥")
    elif savings_balance < high_threshold:
        st.session_state.hp["Savings"] -= 10
    elif savings_balance > high_threshold * 2: # Bonus for high savings
        st.session_state.hp["Savings"] += 10
        st.toast("Savings HP increased! Great buffer!", icon="🎉")
    
    st.session_state.hp["Savings"] = max(0, min(100, st.session_state.hp["Savings"]))

    # 3. Update HP for Debt Accounts
    for card in DEBT_ACCOUNTS:
        debt = st.session_state.accounts[card]
        payment = payments.get(card, 0.0)

        if debt > high_threshold:
            st.session_state.hp[card] -= 25 # High debt penalty
        elif debt > medium_threshold:
            st.session_state.hp[card] -= 10 # Medium debt penalty
        elif debt < 1.0: # Paid off!
            st.session_state.hp[card] += 20 # Big bonus
            if payment > 0: # Only if a payment was made this month
                st.toast(f"{card} is paid off! HP +20!", icon="🥳")
        elif payment > 0:
             st.session_state.hp[card] += 5 # Small bonus for good behavior
        
        # Clamp HP between 0 and 100
        st.session_state.hp[card] = max(0, min(100, st.session_state.hp[card]))


def process_month_end(inputs):
    """
    Main game logic. Takes user inputs, updates state, saves history.
    """
    
    # 1. Calculate totals
    total_payment = inputs['pay_kotak'] + inputs['pay_idfc'] + inputs['pay_supermoney']
    total_expense = inputs['exp_kotak'] + inputs['exp_idfc'] + inputs['exp_supermoney']
    
    # 2. Validate Payments
    if total_payment > st.session_state.accounts["Savings"]:
        st.error(f"Action Failed: Total payment (₹{total_payment:,.2f}) exceeds your savings (₹{st.session_state.accounts['Savings']:,.2f}).")
        return # Stop processing
    
    # 3. Apply New Income
    st.session_state.accounts["Savings"] += inputs['new_savings']
    
    # 4. Apply Payments from Savings
    st.session_state.accounts["Savings"] -= total_payment
    st.session_state.accounts["Kotak"] -= inputs['pay_kotak']
    st.session_state.accounts["IDFC"] -= inputs['pay_idfc']
    st.session_state.accounts["Supermoney"] -= inputs['pay_supermoney']
    
    # 5. Apply New Expenses (Increase Debt)
    st.session_state.accounts["Kotak"] += inputs['exp_kotak']
    st.session_state.accounts["IDFC"] += inputs['exp_idfc']
    st.session_state.accounts["Supermoney"] += inputs['exp_supermoney']

    # 6. Apply Card-to-Card (High Risk)
    card_to_card_payment = inputs['pay_idfc_with_kotak']
    if card_to_card_payment > 0:
        # Validate this payment doesn't exceed debt
        if card_to_card_payment > st.session_state.accounts["IDFC"]:
            st.warning(f"Capping card-to-card payment to IDFC's current debt of ₹{st.session_state.accounts['IDFC']:,.2f}")
            card_to_card_payment = st.session_state.accounts["IDFC"]
            
        st.session_state.accounts["IDFC"] -= card_to_card_payment
        st.session_state.accounts["Kotak"] += card_to_card_payment # Increase Kotak's debt

    # 7. Update HP and Risk
    payments_dict = {
        "Kotak": inputs['pay_kotak'],
        "IDFC": inputs['pay_idfc'],
        "Supermoney": inputs['pay_supermoney']
    }
    update_hp_and_risk(payments_dict, card_to_card_payment)

    # 8. Create new history entry
    new_entry = {
        "Month": st.session_state.month,
        "Savings_Balance": st.session_state.accounts["Savings"],
        "Kotak_Debt": st.session_state.accounts["Kotak"],
        "IDFC_Debt": st.session_state.accounts["IDFC"],
        "Supermoney_Debt": st.session_state.accounts["Supermoney"],
        "Savings_HP": st.session_state.hp["Savings"],
        "Kotak_HP": st.session_state.hp["Kotak"],
        "IDFC_HP": st.session_state.hp["IDFC"],
        "Supermoney_HP": st.session_state.hp["Supermoney"],
        "Risk_Points": st.session_state.risk_points,
        "Total_Payments": total_payment,
        "Total_Expenses": total_expense,
        "New_Income": inputs['new_savings']
    }
    
    # 9. Update session state history and save
    new_df = pd.DataFrame([new_entry])
    st.session_state.history = pd.concat([st.session_state.history, new_df], ignore_index=True)
    save_data()
    
    # 10. Increment month
    st.session_state.month += 1
    
    st.success(f"Month {st.session_state.month - 1} processed! Welcome to Month {st.session_state.month}.")
    st.balloons()
    
    # Rerun to clear forms and show updated overview
    st.rerun()


# --- Main Application UI ---

st.set_page_config(layout="wide", page_title="Expense Management Game")

# --- Sidebar ---
st.sidebar.title("Game Controls")

# Initialize state (must happen before accessing state vars)
initialize_state()

if st.sidebar.button("Reset Game (Deletes History)"):
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    
    # Clear all session state keys
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    st.sidebar.success("Game Reset! Reloading...")
    st.rerun()

st.sidebar.header("Game History")
st.sidebar.dataframe(st.session_state.history.tail(10), use_container_width=True)


# --- Main Page ---

st.title("💸 Expense Management Game 💸")
st.markdown(f"Welcome to **Month: {st.session_state.month}**. Manage your finances and keep your accounts healthy!")

st.divider()

# --- 1. Accounts Overview ---
st.header("📊 Accounts Overview")

cols = st.columns(4)
display_account_card(cols[0], "Savings", st.session_state.accounts['Savings'], st.session_state.hp['Savings'], is_debt=False)
display_account_card(cols[1], "Kotak", st.session_state.accounts['Kotak'], st.session_state.hp['Kotak'], is_debt=True)
display_account_card(cols[2], "IDFC", st.session_state.accounts['IDFC'], st.session_state.hp['IDFC'], is_debt=True)
display_account_card(cols[3], "Supermoney", st.session_state.accounts['Supermoney'], st.session_state.hp['Supermoney'], is_debt=True)

# Risk Points Meter
st.subheader("⚠️ Risk Level")
risk_color = get_color_from_value(st.session_state.risk_points, high_is_bad=True, medium_threshold=50, high_threshold=100)
st.markdown(f"**Risk Points:** <span style='font-size: 24px; color:{risk_color};'>{st.session_state.risk_points}</span>", unsafe_allow_html=True)
st.progress(min(100, st.session_state.risk_points) / 100.0)
if st.session_state.risk_points > 100:
    st.error("DANGER! Your risk level is critical. Avoid using credit to pay credit at all costs!")
elif st.session_state.risk_points > 50:
    st.warning("High Risk! Using credit to pay other credit accounts is unsustainable.")

st.divider()

# --- 2. Monthly Actions ---
st.header("🕹️ Monthly Actions")

with st.form("monthly_actions_form"):
    inputs = {}
    
    st.subheader("💰 Income")
    inputs['new_savings'] = st.number_input(
        "Add to Savings (e.g., Salary) (₹)", 
        min_value=0.0, step=1000.0, value=25000.0,
        help="Money earned this month."
    )

    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💳 Payments from Savings")
        st.caption(f"Max available: ₹{st.session_state.accounts['Savings'] + inputs['new_savings']:,.2f}")
        
        inputs['pay_kotak'] = st.number_input(
            "Pay to Kotak (₹)", min_value=0.0, 
            max_value=st.session_state.accounts['Kotak'], 
            step=100.0,
            help="Cannot pay more than you owe."
        )
        inputs['pay_idfc'] = st.number_input(
            "Pay to IDFC (₹)", min_value=0.0, 
            max_value=st.session_state.accounts['IDFC'], 
            step=100.0
        )
        inputs['pay_supermoney'] = st.number_input(
            "Pay to Supermoney (₹)", min_value=0.0, 
            max_value=st.session_state.accounts['Supermoney'], 
            step=100.0
        )
        
        total_payment = inputs['pay_kotak'] + inputs['pay_idfc'] + inputs['pay_supermoney']
        st.info(f"Total Payment: ₹{total_payment:,.2f}")

    with col2:
        st.subheader("💸 New Expenses")
        st.caption("New debt incurred this month.")
        
        inputs['exp_kotak'] = st.number_input("New Expense on Kotak (₹)", min_value=0.0, step=100.0)
        inputs['exp_idfc'] = st.number_input("New Expense on IDFC (₹)", min_value=0.0, step=100.0)
        inputs['exp_supermoney'] = st.number_input("New Expense on Supermoney (₹)", min_value=0.0, step=100.0)
        
        total_expense = inputs['exp_kotak'] + inputs['exp_idfc'] + inputs['exp_supermoney']
        st.info(f"Total New Expense: ₹{total_expense:,.2f}")

    st.divider()
    
    st.subheader("🔄 Card-to-Card (High Risk!)")
    inputs['pay_idfc_with_kotak'] = st.number_input(
        f"Pay IDFC using Kotak (Max: ₹{st.session_state.accounts['IDFC']:,.2f})", 
        min_value=0.0, 
        max_value=st.session_state.accounts['IDFC'], 
        step=100.0,
        help="This will increase Kotak debt and add 50 Risk Points!"
    )

    submitted = st.form_submit_button(f"End Month {st.session_state.month} & Process Actions")

if submitted:
    process_month_end(inputs)


st.divider()

# --- 3. Visualization ---
st.header("📈 Financial History")

if len(st.session_state.history) < 2:
    st.info("Play a few months to see your history charts.")
else:
    history_df = st.session_state.history.copy()
    
    # Prepare data for plotting
    balances_df = history_df.melt(
        id_vars=['Month'], 
        value_vars=['Savings_Balance', 'Kotak_Debt', 'IDFC_Debt', 'Supermoney_Debt'],
        var_name='Account', 
        value_name='Balance (₹)'
    )
    
    hp_df = history_df.melt(
        id_vars=['Month'], 
        value_vars=['Savings_HP', 'Kotak_HP', 'IDFC_HP', 'Supermoney_HP', 'Risk_Points'],
        var_name='Metric', 
        value_name='Points'
    )
    
    flows_df = history_df.melt(
        id_vars=['Month'],
        value_vars=['Total_Payments', 'Total_Expenses', 'New_Income'],
        var_name='Flow',
        value_name='Amount (₹)'
    )

    # Chart 1: Account Balances Over Time
    st.subheader("Account Balances Over Time")
    balance_chart = alt.Chart(balances_df).mark_line(point=True).encode(
        x=alt.X('Month', axis=alt.Axis(format='d')), # Format as integer
        y=alt.Y('Balance (₹)', title='Balance (₹)'),
        color='Account',
        tooltip=['Month', 'Account', 'Balance (₹)']
    ).interactive()
    st.altair_chart(balance_chart, use_container_width=True)
    
    # Chart 2: Monthly Flows (Payments vs Expenses)
    st.subheader("Monthly Income vs. Payments vs. Expenses")
    flow_chart = alt.Chart(flows_df).mark_bar().encode(
        x=alt.X('Month:O', axis=alt.Axis(title='Month')), # Treat month as ordinal
        y=alt.Y('Amount (₹)', title='Amount (₹)'),
        color='Flow',
        xOffset='Flow',
        tooltip=['Month', 'Flow', 'Amount (₹)']
    ).interactive()
    st.altair_chart(flow_chart, use_container_width=True)

    # Chart 3: Health & Risk Over Time
    st.subheader("Health & Risk Over Time")
    hp_chart = alt.Chart(hp_df).mark_line(point=True).encode(
        x=alt.X('Month', axis=alt.Axis(format='d')),
        y=alt.Y('Points', title='Points (HP / Risk)'),
        color='Metric',
        tooltip=['Month', 'Metric', 'Points']
    ).interactive()
    st.altair_chart(hp_chart, use_container_width=True)

    # Show raw data history
    with st.expander("View Raw History Data"):
        st.dataframe(st.session_state.history, use_container_width=True)


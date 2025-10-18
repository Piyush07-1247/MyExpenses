# app.py
# A personal finance "game" for managing credit card debt.
# To run:
# 1. Save this file as app.py
# 2. Make sure you have streamlit and pandas:
#    pip install streamlit pandas altair
# 3. In your terminal, run:
#    streamlit run app.py

import streamlit as st
import pandas as pd
import altair as alt
import os

# --- Constants ---
HISTORY_FILE = "cc_game_history.csv"
CC_ACCOUNTS = ["Kotak", "IDFC", "Super"]
ALL_ACCOUNTS = ["Savings"] + CC_ACCOUNTS

# --- Utility Functions ---

def get_utilization_color(usage_pct):
    """Returns a color based on credit utilization percentage."""
    if usage_pct > 80:
        return "red"
    elif usage_pct > 50:
        return "orange"
    else:
        return "green"

def get_hp_color(hp):
    """Returns a color for HP."""
    if hp < 30:
        return "red"
    elif hp < 70:
        return "orange"
    else:
        return "green"

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
        "Savings_Balance", "Savings_HP",
        "Kotak_Debt", "Kotak_Due", "Kotak_HP",
        "IDFC_Debt", "IDFC_Due", "IDFC_HP",
        "Super_Debt", "Super_Due", "Super_HP",
        "Risk_Points",
        "Total_Paid_From_Savings", "Total_Balance_Transfers", "Total_New_Expenses"
    ]
    return pd.DataFrame(columns=columns)

def save_data():
    """Saves the session state history to CSV."""
    st.session_state.history.to_csv(HISTORY_FILE, index=False)

def initialize_state(setup_data):
    """
    Initializes or resets the game state based on sidebar setup.
    This function is called when the 'Start/Reset Game' button is pressed.
    """
    
    # 1. Clear existing history file
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
        
    # 2. Set game settings
    st.session_state.min_payment_pct = setup_data['min_payment_pct']
    st.session_state.high_debt_pct = setup_data['high_debt_pct']
    
    # 3. Initialize game state
    st.session_state.month = 1
    st.session_state.risk_points = 0
    st.session_state.accounts = {
        "Savings": {
            "balance": setup_data['savings_balance'],
            "hp": 100
        },
        "Kotak": {
            "full_limit": setup_data['kotak_limit'],
            "current_debt": setup_data['kotak_debt'],
            "month_due": setup_data['kotak_due'],
            "hp": 100
        },
        "IDFC": {
            "full_limit": setup_data['idfc_limit'],
            "current_debt": setup_data['idfc_debt'],
            "month_due": setup_data['idfc_due'],
            "hp": 100
        },
        "Super": {
            "full_limit": setup_data['super_limit'],
            "current_debt": setup_data['super_debt'],
            "month_due": setup_data['super_due'],
            "hp": 100
        }
    }
    
    # 4. Create first history entry (Month 0 / Start)
    initial_entry = {
        "Month": 0,
        "Savings_Balance": setup_data['savings_balance'], "Savings_HP": 100,
        "Kotak_Debt": setup_data['kotak_debt'], "Kotak_Due": setup_data['kotak_due'], "Kotak_HP": 100,
        "IDFC_Debt": setup_data['idfc_debt'], "IDFC_Due": setup_data['idfc_due'], "IDFC_HP": 100,
        "Super_Debt": setup_data['super_debt'], "Super_Due": setup_data['super_due'], "Super_HP": 100,
        "Risk_Points": 0,
        "Total_Paid_From_Savings": 0.0, "Total_Balance_Transfers": 0.0, "Total_New_Expenses": 0.0
    }
    st.session_state.history = pd.DataFrame([initial_entry])
    save_data()
    
    st.session_state.game_started = True
    st.success("Game Started! History has been reset.")


def load_from_history():
    """Loads the last known state from the CSV file."""
    if 'game_started' in st.session_state:
        return # Game is already running

    history_df = load_data()
    if not history_df.empty:
        last_row = history_df.iloc[-1]
        
        # Load settings (if they exist, otherwise use defaults)
        st.session_state.min_payment_pct = st.sidebar.number_input("Min. Payment %", 1, 20, 5)
        st.session_state.high_debt_pct = st.sidebar.number_input("High Debt % Threshold", 50, 100, 80)

        st.session_state.month = int(last_row["Month"]) + 1
        st.session_state.risk_points = int(last_row["Risk_Points"])
        st.session_state.accounts = {
            "Savings": {
                "balance": last_row["Savings_Balance"],
                "hp": last_row["Savings_HP"]
            },
            "Kotak": {
                "full_limit": st.session_state.get('kotak_full_limit', last_row["Kotak_Debt"] * 2), # Estimate if not set
                "current_debt": last_row["Kotak_Debt"],
                "month_due": last_row["Kotak_Due"],
                "hp": last_row["Kotak_HP"]
            },
            "IDFC": {
                "full_limit": st.session_state.get('idfc_full_limit', last_row["IDFC_Debt"] * 2),
                "current_debt": last_row["IDFC_Debt"],
                "month_due": last_row["IDFC_Due"],
                "hp": last_row["IDFC_HP"]
            },
            "Super": {
                "full_limit": st.session_state.get('super_full_limit', last_row["Super_Debt"] * 2),
                "current_debt": last_row["Super_Debt"],
                "month_due": last_row["Super_Due"],
                "hp": last_row["Super_HP"]
            }
        }
        
        # Need to store full limits in state to persist them
        st.session_state.kotak_full_limit = st.session_state.accounts["Kotak"]["full_limit"]
        st.session_state.idfc_full_limit = st.session_state.accounts["IDFC"]["full_limit"]
        st.session_state.super_full_limit = st.session_state.accounts["Super"]["full_limit"]

        st.session_state.history = history_df
        st.session_state.game_started = True
    

def display_cc_card(col, name):
    """Renders a single CC info card in a Streamlit column."""
    acc = st.session_state.accounts[name]
    
    limit = acc['full_limit']
    debt = acc['current_debt']
    due = acc['month_due']
    hp = acc['hp']
    
    available = limit - debt
    usage_pct = (debt / limit) * 100 if limit > 0 else 0
    color = get_utilization_color(usage_pct)
    
    with col:
        st.subheader(f"💳 {name} CC")
        st.metric(
            label="Current Debt (₹)",
            value=f"{debt:,.2f}",
            delta=f"Full Limit: {limit:,.2f}",
            delta_color="off"
        )
        st.metric(
            label="Month Due (₹)",
            value=f"{due:,.2f}",
            delta=f"HP: {hp}",
            delta_color=get_hp_color(hp)
        )
        st.metric(
            label="Limit Available (₹)",
            value=f"{available:,.2f}",
            delta=f"{usage_pct:.1f}% Utilized",
            delta_color="inverse" if usage_pct > st.session_state.high_debt_pct else "normal"
        )
        # Custom colored progress bar
        st.markdown(f"""
        <div style="background: #f0f2f6; border-radius: 5px; height: 10px; margin-top: -10px;">
            <div style="width: {usage_pct}%; background-color: {color}; height: 10px; border-radius: 5px;"></div>
        </div>
        """, unsafe_allow_html=True)

def process_month_end(inputs):
    """Main game logic to process the month-end form."""
    
    acc_state = st.session_state.accounts
    
    # Store original due amounts to check if they were paid
    original_due = {
        "Kotak": acc_state["Kotak"]["month_due"],
        "IDFC": acc_state["IDFC"]["month_due"],
        "Super": acc_state["Super"]["month_due"]
    }
    
    paid_this_month = { "Kotak": 0.0, "IDFC": 0.0, "Super": 0.0 }
    total_paid_from_savings = 0.0
    total_balance_transfers = 0.0
    total_new_expenses = 0.0
    
    # --- 1. Add Income ---
    acc_state["Savings"]["balance"] += inputs['new_income']
    
    # --- 2. Process Payments from Savings ---
    total_from_savings = inputs['pay_kotak_sav'] + inputs['pay_idfc_sav'] + inputs['pay_super_sav']
    if total_from_savings > acc_state["Savings"]["balance"]:
        st.error(f"Action Failed: Total payment from savings (₹{total_from_savings:,.2f}) exceeds available savings (₹{acc_state['Savings']['balance']:,.2f}).")
        return
        
    acc_state["Savings"]["balance"] -= total_from_savings
    total_paid_from_savings = total_from_savings
    
    acc_state["Kotak"]["current_debt"] -= inputs['pay_kotak_sav']
    paid_this_month["Kotak"] += inputs['pay_kotak_sav']
    
    acc_state["IDFC"]["current_debt"] -= inputs['pay_idfc_sav']
    paid_this_month["IDFC"] += inputs['pay_idfc_sav']
    
    acc_state["Super"]["current_debt"] -= inputs['pay_super_sav']
    paid_this_month["Super"] += inputs['pay_super_sav']
    
    # --- 3. Process Balance Transfers (High Risk!) ---
    # We must process these one by one, checking available limit each time
    
    # Pay Kotak
    for source_card in ["IDFC", "Super"]:
        payment = inputs[f'pay_kotak_from_{source_card.lower()}']
        if payment > 0:
            source_acc = acc_state[source_card]
            available = source_acc['full_limit'] - source_acc['current_debt']
            if payment > available:
                st.error(f"Failed: Payment from {source_card} (₹{payment:,.2f}) exceeds its available limit (₹{available:,.2f}).")
                return
            
            source_acc['current_debt'] += payment # Increase source debt
            acc_state["Kotak"]["current_debt"] -= payment # Decrease target debt
            paid_this_month["Kotak"] += payment
            total_balance_transfers += payment
            st.session_state.risk_points += 25 # Penalty

    # Pay IDFC
    for source_card in ["Kotak", "Super"]:
        payment = inputs[f'pay_idfc_from_{source_card.lower()}']
        if payment > 0:
            source_acc = acc_state[source_card]
            available = source_acc['full_limit'] - source_acc['current_debt']
            if payment > available:
                st.error(f"Failed: Payment from {source_card} (₹{payment:,.2f}) exceeds its available limit (₹{available:,.2f}).")
                return
            
            source_acc['current_debt'] += payment
            acc_state["IDFC"]["current_debt"] -= payment
            paid_this_month["IDFC"] += payment
            total_balance_transfers += payment
            st.session_state.risk_points += 25

    # Pay Super
    for source_card in ["Kotak", "IDFC"]:
        payment = inputs[f'pay_super_from_{source_card.lower()}']
        if payment > 0:
            source_acc = acc_state[source_card]
            available = source_acc['full_limit'] - source_acc['current_debt']
            if payment > available:
                st.error(f"Failed: Payment from {source_card} (₹{payment:,.2f}) exceeds its available limit (₹{available:,.2f}).")
                return
            
            source_acc['current_debt'] += payment
            acc_state["Super"]["current_debt"] -= payment
            paid_this_month["Super"] += payment
            total_balance_transfers += payment
            st.session_state.risk_points += 25
            
    if total_balance_transfers > 0:
        st.warning(f"High Risk! You transferred ₹{total_balance_transfers:,.2f} between cards, gaining {st.session_state.risk_points} Risk Points!")

    # --- 4. Process New Expenses ---
    for card in CC_ACCOUNTS:
        expense = inputs[f'exp_{card.lower()}']
        if expense > 0:
            acc = acc_state[card]
            available = acc['full_limit'] - acc['current_debt']
            if expense > available:
                st.error(f"Failed: New expense on {card} (₹{expense:,.2f}) exceeds its available limit (₹{available:,.2f}).")
                return
            acc['current_debt'] += expense
            total_new_expenses += expense

    # --- 5. Update HP and Risk ---
    
    # Risk decay
    st.session_state.risk_points = max(0, st.session_state.risk_points - 10)

    # Savings HP
    if acc_state["Savings"]["balance"] < 5000:
        acc_state["Savings"]["hp"] = max(0, acc_state["Savings"]["hp"] - 20)
    elif acc_state["Savings"]["balance"] > 100000:
        acc_state["Savings"]["hp"] = min(100, acc_state["Savings"]["hp"] + 10)
    else:
        acc_state["Savings"]["hp"] = min(100, acc_state["Savings"]["hp"] + 2)

    # CC HP
    for card in CC_ACCOUNTS:
        acc = acc_state[card]
        
        # Penalty for not paying the minimum
        if paid_this_month[card] < original_due[card]:
            acc['hp'] = max(0, acc['hp'] - 50)
            st.toast(f"Critical! {card} minimum due was not paid! HP -50", icon="🔥")
        else:
            acc['hp'] = min(100, acc['hp'] + 10) # Bonus for paying due
        
        # Penalty for high utilization
        usage_pct = (acc['current_debt'] / acc['full_limit']) * 100
        if usage_pct > st.session_state.high_debt_pct:
            acc['hp'] = max(0, acc['hp'] - 20)
            st.toast(f"{card} utilization is over {st.session_state.high_debt_pct}%! HP -20", icon="😥")
        
        # Bonus for low utilization
        if usage_pct < 10 and acc['current_debt'] > 0:
            acc['hp'] = min(100, acc['hp'] + 5)
            
    # --- 6. Calculate Next Month's Due ---
    min_pay_pct = st.session_state.min_payment_pct / 100.0
    for card in CC_ACCOUNTS:
        # Simplified: new due is a % of the new outstanding debt.
        # A real game might add interest here too!
        acc_state[card]["month_due"] = max(0, acc_state[card]["current_debt"] * min_pay_pct)

    # --- 7. Save to History ---
    new_entry = {
        "Month": st.session_state.month,
        "Savings_Balance": acc_state["Savings"]["balance"], "Savings_HP": acc_state["Savings"]["hp"],
        "Kotak_Debt": acc_state["Kotak"]["current_debt"], "Kotak_Due": acc_state["Kotak"]["month_due"], "Kotak_HP": acc_state["Kotak"]["hp"],
        "IDFC_Debt": acc_state["IDFC"]["current_debt"], "IDFC_Due": acc_state["IDFC"]["month_due"], "IDFC_HP": acc_state["IDFC"]["hp"],
        "Super_Debt": acc_state["Super"]["current_debt"], "Super_Due": acc_state["Super"]["month_due"], "Super_HP": acc_state["Super"]["hp"],
        "Risk_Points": st.session_state.risk_points,
        "Total_Paid_From_Savings": total_paid_from_savings, 
        "Total_Balance_Transfers": total_balance_transfers, 
        "Total_New_Expenses": total_new_expenses
    }
    
    new_df = pd.DataFrame([new_entry])
    st.session_state.history = pd.concat([st.session_state.history, new_df], ignore_index=True)
    save_data()
    
    # --- 8. Increment Month and Rerun ---
    st.session_state.month += 1
    st.success(f"Month {st.session_state.month - 1} processed! Welcome to Month {st.session_state.month}.")
    st.balloons()
    st.rerun()

# ==================================================================
#                        STREAMLIT UI
# ==================================================================

st.set_page_config(layout="wide", page_title="CC Debt Management Game")

# --- Sidebar ---
st.sidebar.title("Game Setup & Controls")
st.sidebar.markdown("Set your initial financial state. Pressing 'Start' will **delete all history**.")

with st.sidebar.expander("Game Settings"):
    settings = {
        'min_payment_pct': st.number_input("Min. Payment %", 1, 20, 5, 
                                           help="The minimum % of debt that becomes 'Due' each month."),
        'high_debt_pct': st.number_input("High Debt % Threshold", 50, 100, 80, 
                                        help="Utilization % above this will appear RED and cause HP loss.")
    }

with st.sidebar.form("setup_form"):
    st.subheader("💰 Savings Account")
    setup_inputs = {
        'savings_balance': st.number_input("Current Savings Balance (₹)", 0.0, step=1000.0)
    }
    
    st.subheader("💳 Kotak CC")
    setup_inputs['kotak_limit'] = st.number_input("Kotak: Full Limit (₹)", 1.0, step=1000.0)
    setup_inputs['kotak_debt'] = st.number_input("Kotak: Current Debt (₹)", 0.0, step=100.0)
    setup_inputs['kotak_due'] = st.number_input("Kotak: Month Due (₹)", 0.0, step=100.0)
    
    st.subheader("💳 IDFC CC")
    setup_inputs['idfc_limit'] = st.number_input("IDFC: Full Limit (₹)", 1.0, step=1000.0)
    setup_inputs['idfc_debt'] = st.number_input("IDFC: Current Debt (₹)", 0.0, step=100.0)
    setup_inputs['idfc_due'] = st.number_input("IDFC: Month Due (₹)", 0.0, step=100.0)
    
    st.subheader("💳 Super CC")
    setup_inputs['super_limit'] = st.number_input("Super: Full Limit (₹)", 1.0, step=1000.0)
    setup_inputs['super_debt'] = st.number_input("Super: Current Debt (₹)", 0.0, step=100.0)
    setup_inputs['super_due'] = st.number_input("Super: Month Due (₹)", 0.0, step=100.0)
    
    # Add settings to setup data
    setup_inputs.update(settings)
    
    submitted_setup = st.form_submit_button("Start / Reset Game")

if submitted_setup:
    # Store full limits in session state so they persist when loading
    st.session_state.kotak_full_limit = setup_inputs['kotak_limit']
    st.session_state.idfc_full_limit = setup_inputs['idfc_limit']
    st.session_state.super_full_limit = setup_inputs['super_limit']
    initialize_state(setup_inputs)
    st.rerun()

# Try to load from history if game hasn't been started from sidebar
if 'game_started' not in st.session_state:
    load_from_history()


# --- Main Page ---

if 'game_started' not in st.session_state:
    st.title("💸 Welcome to the CC Debt Management Game 💸")
    st.info("Please set up your accounts in the sidebar and press 'Start Game' to begin.")
else:
    st.title(f"💸 CC Debt Management: Month {st.session_state.month} 💸")
    
    # --- 1. Accounts Overview ---
    st.header("📊 Accounts Overview")
    
    cols = st.columns(4)
    with cols[0]:
        st.subheader("💰 Savings")
        st.metric(
            label="Current Balance (₹)",
            value=f"{st.session_state.accounts['Savings']['balance']:,.2f}",
            delta=f"HP: {st.session_state.accounts['Savings']['hp']}",
            delta_color=get_hp_color(st.session_state.accounts['Savings']['hp'])
        )

    display_cc_card(cols[1], "Kotak")
    display_cc_card(cols[2], "IDFC")
    display_cc_card(cols[3], "Super")

    # Risk Points Meter
    st.subheader("⚠️ Risk Level")
    risk_color = "red" if st.session_state.risk_points > 100 else ("orange" if st.session_state.risk_points > 50 else "green")
    st.markdown(f"**Risk Points:** <span style='font-size: 24px; color:{risk_color};'>{st.session_state.risk_points}</span>", unsafe_allow_html=True)
    st.progress(min(100, st.session_state.risk_points) / 100.0)
    if st.session_state.risk_points > 50:
        st.warning("High Risk! Using credit to pay credit is unsustainable.")

    st.divider()

    # --- 2. Monthly Actions ---
    st.header("🕹️ Monthly Actions")
    with st.form("monthly_actions_form"):
        form_inputs = {}
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("💰 Income & 💸 Expenses")
            form_inputs['new_income'] = st.number_input("New Income to Savings (₹)", 0.0, step=1000.0)
            st.divider()
            form_inputs['exp_kotak'] = st.number_input("New Expense on Kotak (₹)", 0.0, step=100.0)
            form_inputs['exp_idfc'] = st.number_input("New Expense on IDFC (₹)", 0.0, step=100.0)
            form_inputs['exp_super'] = st.number_input("New Expense on Super (₹)", 0.0, step=100.0)
            
        with c2:
            st.subheader("💳 Payments from Savings")
            st.caption(f"Available: ₹{st.session_state.accounts['Savings']['balance'] + form_inputs['new_income']:,.2f}")
            form_inputs['pay_kotak_sav'] = st.number_input("Pay Kotak from Savings (₹)", 0.0, step=10

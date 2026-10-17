
from datetime import date
from gspread_dataframe import set_with_dataframe
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Farm Labor & Expense Tracker", page_icon="🌾", layout="centered"
)

st.title("🌾 Farm Daily Log & Expenses")
st.write(
    "Shared family app for tracking daily labor, wages, and farm expenses."
)

# Connect to Google Sheets using Streamlit's native connection
try:
  conn = st.connection("gsheets", type="GSheetsConnection")
  # Read existing data from the sheet named Farm_Labor_Expenses
  df_data = conn.read(worksheet="Sheet1", ttl=0)
except Exception as e:
  st.error(
      "⚠️ Database connection failed. Please make sure [connections.gsheets]"
      " is set up in Secrets."
  )
  st.stop()

# User selection
st.sidebar.header("User Profile")
current_user = st.sidebar.selectbox(
    "Who is making this entry?", ["Pavan", "Dad", "Brother"]
)

# Main Entry Form
with st.form("expense_form", clear_on_submit=True):
  st.subheader("➕ Add New Entry")

  col1, col2 = st.columns(2)
  with col1:
    entry_date = st.date_input("Date", date.today())
  with col2:
    entry_type = st.selectbox(
        "Type", ["Labor Wage", "Material/Fertilizer", "General Farm Expense"]
    )

  name_details = st.text_input(
      "Worker Name / Item Description",
      placeholder="e.g., Ramaiah (Labor) or Potash Fertilizer",
  )
  amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
  notes = st.text_area(
      "Notes (Optional)", placeholder="e.g., Worked on Arecanut plot"
  )

  submitted = st.form_submit_button("Save Entry")

  if submitted:
    if not name_details or amount <= 0:
      st.warning(
          "Please fill in the worker name/description and a valid amount."
      )
    else:
      # Append new row using the connection
      new_row = pd.DataFrame([{
          "Date": str(entry_date),
          "Added_By": current_user,
          "Category": entry_type,
          "Name_or_Details": name_details,
          "Amount": amount,
          "Notes": notes,
      }])
      updated_df = pd.concat([df_data, new_row], ignore_index=True)
      conn.update(worksheet="Sheet1", data=updated_df)
      st.success(f"✅ Entry saved successfully by {current_user}!")
      st.rerun()

st.markdown("---")
st.subheader("📊 Recent Records & Summary")

if df_data is not None and not df_data.empty:
  if "Amount" in df_data.columns:
    total_spent = df_data["Amount"].sum()
    st.metric(label="Total Expenses Recorded", value=f"₹ {total_spent:,.2f}")
  st.dataframe(df_data, use_container_width=True)
else:
  st.info("No entries yet. Fill out the form above to add your first record!")

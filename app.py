from datetime import date
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Farm Labor & Expense Tracker", page_icon="🌾", layout="centered"
)

st.title("🌾 Farm Daily Log & Expenses")
st.write(
    "Shared family app for tracking daily labor, wages, and farm expenses."
)


@st.cache_resource
def init_google_sheets():
  try:
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_dict:
      creds_dict["private_key"] = creds_dict["private_key"].replace(
          "\\n", "\n"
      )

    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    # Open directly using your spreadsheet ID
    sheet = client.open_by_key(
        "1CaVmS0UFlw3pFab_DzxxcSODbaIKzWoyxdyR2FvFvfc"
    ).sheet1
    return sheet, None
  except Exception as e:
    # This will show the exact error name and details on your screen
    return None, f"{type(e).__name__}: {str(e)}"


sheet, error_msg = init_google_sheets()

if error_msg:
  st.error(f"⚠️ Detailed Error: {error_msg}")
  st.info(
      "💡 Tip: If this says 'SpreadsheetNotFound', make sure your Google Sheet"
      " is shared with: farm-app-account@neon-reporter-457403-d3.iam.gserviceaccount.com"
  )
  st.stop()

# User selection
st.sidebar.header("User Profile")
current_user = st.sidebar.selectbox(
    "Who is making this entry?", ["Pavan", "Dad", "Brother"]
)

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
      row_data = [
          str(entry_date),
          current_user,
          entry_type,
          name_details,
          amount,
          notes,
      ]
      sheet.append_row(row_data)
      st.success(f"✅ Entry saved successfully by {current_user}!")
      st.rerun()

st.markdown("---")
st.subheader("📊 Recent Records & Summary")

try:
  data = sheet.get_all_records()
  df = pd.DataFrame(data)

  if not df.empty and "Amount" in df.columns:
    total_spent = df["Amount"].sum()
    st.metric(label="Total Expenses Recorded", value=f"₹ {total_spent:,.2f}")
    st.dataframe(df, use_container_width=True)
  else:
    st.info("No entries yet. Fill out the form above to add your first record!")
except Exception as e:
  st.info(
      "Sheet is connected successfully! Add your first record above to start"
      " tracking."
  )


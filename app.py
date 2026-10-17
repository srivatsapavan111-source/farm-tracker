from datetime import date
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Farm Labor & Expense Tracker", page_icon="🌾", layout="centered"
)

st.title("🌾 Farm Daily Log & Expenses")


@st.cache_resource
def init_google_sheets():
  scope = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive",
  ]
  creds_dict = dict(st.secrets["gcp_service_account"])
  if "private_key" in creds_dict:
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

  creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
  client = gspread.authorize(creds)
  sheet = client.open_by_key(
      "1CaVmS0UFlw3pFab_DzxxcSODbaIKzWoyxdyR2FvFvfc"
  ).sheet1
  return sheet


try:
  sheet = init_google_sheets()
except Exception as e:
  st.error(f"⚠️ Connection Error: {e}")
  st.stop()

# User selection
st.sidebar.header("User Profile")
current_user = st.sidebar.selectbox(
    "Who is making this entry?", ["Pavan", "Dad", "Brother"]
)

# Navigation Tabs
tab1, tab2 = st.tabs(["➕ Add Entry", "✏️ View / Edit / Delete Records"])

# --- TAB 1: ADD ENTRY ---
with tab1:
  with st.form("expense_form", clear_on_submit=True):
    st.subheader("Add New Daily Record")

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

# --- TAB 2: VIEW, EDIT & DELETE ---
with tab2:
  st.subheader("Manage Past Records")

  try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
      total_spent = (
          df["Amount"].sum() if "Amount" in df.columns else 0.0
      )
      st.metric(label="Total Expenses Recorded", value=f"₹ {total_spent:,.2f}")

      # Show table with row indices so user knows which row to edit/delete
      df_display = df.copy()
      df_display.insert(0, "Row_ID", range(2, len(df) + 2))  
      # Row 2 corresponds to Google Sheets row index (since row 1 is headers)

      st.dataframe(df_display, use_container_width=True)

      st.markdown("---")
      st.write("### Modify or Delete an Entry")

      # Pick a row to modify based on row ID
      row_options = list(range(2, len(df) + 2))
      selected_row = st.selectbox("Select Row ID to Edit or Delete", row_options)

      # Get current values of that row
      row_idx = selected_row - 2
      curr_date = df.loc[row_idx, "Date"] if "Date" in df.columns else ""
      curr_user = (
          df.loc[row_idx, "Added_By"] if "Added_By" in df.columns else ""
      )
      curr_type = df.loc[row_idx, "Category"] if "Category" in df.columns else ""
      curr_desc = (
          df.loc[row_idx, "Name_or_Details"]
          if "Name_or_Details" in df.columns
          else ""
      )
      curr_amt = df.loc[row_idx, "Amount"] if "Amount" in df.columns else 0.0
      curr_notes = df.loc[row_idx, "Notes"] if "Notes" in df.columns else ""

      with st.form("edit_form"):
        new_date = st.text_input("Date (YYYY-MM-DD)", value=str(curr_date))
        new_type = st.selectbox(
            "Type",
            [
                "Labor Wage",
                "Material/Fertilizer",
                "General Farm Expense",
            ],
            index=(
                [
                    "Labor Wage",
                    "Material/Fertilizer",
                    "General Farm Expense",
                ].index(curr_type)
                if curr_type
                in [
                    "Labor Wage",
                    "Material/Fertilizer",
                    "General Farm Expense",
                ]
                else 0
            ),
        )
        new_desc = st.text_input("Worker Name / Description", value=str(curr_desc))
        new_amt = st.number_input("Amount (₹)", value=float(curr_amt))
        new_notes = st.text_area("Notes", value=str(curr_notes))

        col_update, col_delete = st.columns(2)
        update_btn = col_update.form_submit_button("💾 Update Row")
        delete_btn = col_delete.form_submit_button("🗑️ Delete Row")

        if update_btn:
          # Update row in Google Sheets (Row index in gspread starts at 1, headers are row 1)
          updated_values = [
              new_date,
              curr_user,
              new_type,
              new_desc,
              new_amt,
              new_notes,
          ]
          sheet.row_values(selected_row)  # safety check
          sheet.update(f"A{selected_row}:F{selected_row}", [updated_values])
          st.success(f"Successfully updated Row {selected_row}!")
          st.rerun()

        if delete_btn:
          sheet.delete_rows(selected_row)
          st.warning(f"Successfully deleted Row {selected_row}!")
          st.rerun()

    else:
      st.info("No entries found to manage.")
  except Exception as e:
     st.info("Loading records or sheet is empty...")


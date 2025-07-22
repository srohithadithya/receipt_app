import streamlit as st
import pandas as pd
from ui.auth_manager import AuthManager
from database.crud import get_receipts_by_user, update_receipt, delete_receipt, get_all_vendors, get_all_categories
from database.database import get_db
from processing.algorithms.search import linear_search_records, range_search_records, pattern_search_records, HashedIndex
from processing.algorithms.sort import sort_records
from ui.components import display_records_table
from utils.helpers import convert_df_to_csv, convert_df_to_json
from datetime import date, datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_records_page():
    auth_manager = AuthManager()
    auth_manager.require_login()

    user_id = auth_manager.get_current_user_id()
    st.title("📋 Your Transaction Records")
    st.markdown("Manage, search, and sort your digitized receipts and bills.")

    db_gen = get_db()
    db = next(db_gen)
    receipts_db_objects = get_receipts_by_user(db, user_id, limit=None) # Fetch all for current user

    # Get mappings for display
    vendors_map = {v.id: v.name for v in get_all_vendors(db)}
    categories_map = {c.id: c.name for c in get_all_categories(db)}
    db.close()

    if not receipts_db_objects:
        st.info("No records found for your account. Start by uploading receipts!")
        if st.button("Go to Upload Page"):
            st.session_state["main_nav_radio"] = "Upload Receipt" # Corrected session state key
            st.rerun()
        return

    # Convert SQLAlchemy objects to a list of dicts for easier DataFrame conversion
    records_list = []
    for r in receipts_db_objects:
        records_list.append({
            "id": r.id,
            "vendor_id": r.vendor_id, # Keep ID for update, display name
            "vendor_name": vendors_map.get(r.vendor_id, "Unknown"),
            "transaction_date": r.transaction_date,
            "billing_period_start": r.billing_period_start,
            "billing_period_end": r.billing_period_end,
            "amount": r.amount,
            "currency": r.currency,
            "category_id": r.category_id, # Keep ID for update, display name
            "category_name": categories_map.get(r.category_id, "Uncategorized"),
            "original_filename": r.original_filename,
            "parsed_raw_text": r.parsed_raw_text,
            "upload_date": r.upload_date
        })

    df = pd.DataFrame(records_list)

    # --- Search, Sort, Filter Controls ---
    st.sidebar.header("Filter & Sort Options")

    # Search
    search_query = st.sidebar.text_input("Keyword Search", help="Search across Vendor, Category, and Filename.")
    if search_query:
        df = linear_search_records(df.to_dict('records'), search_query,
                                   fields=["vendor_name", "category_name", "original_filename", "parsed_raw_text"])
        df = pd.DataFrame(df) # Convert back to DataFrame
        if df.empty:
            st.warning("No records match your search query.")

    # Range Search for Amount
    st.sidebar.subheader("Amount Range")
    min_amount = st.sidebar.number_input("Min Amount", value=float(df['amount'].min()) if not df.empty else 0.0, step=0.1)
    max_amount = st.sidebar.number_input("Max Amount", value=float(df['amount'].max()) if not df.empty else 1000.0, step=0.1)
    if min_amount != float(df['amount'].min()) or max_amount != float(df['amount'].max()) or (min_amount > 0 or max_amount < 1000.0): # Only filter if values changed from default or specific range applied
        df = range_search_records(df.to_dict('records'), "amount", min_amount, max_amount)
        df = pd.DataFrame(df)
        if df.empty:
            st.warning("No records match the amount range.")

    # Sort
    sort_options = {
        "Transaction Date": "transaction_date",
        "Upload Date": "upload_date",
        "Amount": "amount",
        "Vendor Name": "vendor_name",
        "Category Name": "category_name"
    }
    selected_sort_key_display = st.sidebar.selectbox("Sort By", list(sort_options.keys()))
    sort_key = sort_options[selected_sort_key_display]
    sort_order = st.sidebar.radio("Order", ["Descending", "Ascending"])
    reverse_sort = (sort_order == "Descending")

    if not df.empty:
        df = sort_records(df.to_dict('records'), sort_key, reverse_sort, algorithm="timsort")
        df = pd.DataFrame(df)


    st.subheader(f"Total Filtered Records: {len(df)}")
    display_records_table(df, key="records_display_table")

    st.markdown("---")

    # --- Manual Correction & Deletion ---
    st.header("Manual Correction & Actions")
    st.info("Select a record's ID below to update its fields or delete it.")

    record_ids = df['id'].tolist()
    if record_ids:
        # Pre-select the first ID or None
        selected_record_id = st.selectbox("Select Record ID for Action", options=[None] + record_ids, format_func=lambda x: f"ID: {x}" if x else "Select a record...")
    else:
        selected_record_id = None
        st.warning("No records available to select for action.")

    if selected_record_id:
        selected_record = df[df['id'] == selected_record_id].iloc[0].to_dict()

        st.subheader(f"Editing Record ID: {selected_record_id}")
        with st.form(key=f"edit_record_form_{selected_record_id}"):
            # Pre-fill with current values
            new_vendor_name = st.text_input("Vendor Name", value=selected_record.get("vendor_name", ""), key=f"vendor_{selected_record_id}")
            new_transaction_date = st.date_input("Transaction Date", value=selected_record.get("transaction_date", date.today()), key=f"date_{selected_record_id}")
            new_amount = st.number_input("Amount", value=float(selected_record.get("amount", 0.0)), step=0.01, format="%.2f", key=f"amount_{selected_record_id}")
            new_currency = st.text_input("Currency", value=selected_record.get("currency", "USD"), key=f"currency_{selected_record_id}")

            # Get all available categories for dropdown
            db_gen_cat = get_db()
            db_cat = next(db_gen_cat)
            all_categories = get_all_categories(db_cat)
            db_cat.close()
            category_options = [""] + [cat.name for cat in all_categories] # Add empty for uncategorized
            current_category_name = selected_record.get("category_name", "")
            selected_category_index = category_options.index(current_category_name) if current_category_name in category_options else 0
            new_category_name = st.selectbox("Category", options=category_options, index=selected_category_index, key=f"category_{selected_record_id}")

            # Ensure date inputs handle None for optional fields gracefully
            bp_start_value = selected_record.get("billing_period_start")
            bp_end_value = selected_record.get("billing_period_end")
            new_billing_period_start = st.date_input("Billing Period Start (Optional)", value=bp_start_value if bp_start_value else None, key=f"bp_start_{selected_record_id}")
            new_billing_period_end = st.date_input("Billing Period End (Optional)", value=bp_end_value if bp_end_value else None, key=f"bp_end_{selected_record_id}")

            new_original_filename = st.text_input("Original Filename", value=selected_record.get("original_filename", ""), key=f"filename_{selected_record_id}", disabled=True)
            st.text_area("Parsed Raw Text (Read-only)", value=selected_record.get("parsed_raw_text", "N/A"), height=150, disabled=True)

            col_edit, col_delete = st.columns(2)
            with col_edit:
                update_button = st.form_submit_button("Update Record")
            with col_delete:
                delete_button_trigger = st.form_submit_button("Delete Record", type="secondary") # Use secondary for destructive action

            if update_button:
                db_gen_update = get_db()
                db_update = next(db_gen_update)
                try:
                    update_data = {
                        "vendor_name": new_vendor_name,
                        "transaction_date": new_transaction_date,
                        "amount": new_amount,
                        "currency": new_currency,
                        "category_name": new_category_name if new_category_name else None,
                        "billing_period_start": new_billing_period_start,
                        "billing_period_end": new_billing_period_end
                    }
                    updated_record = update_receipt(db_update, selected_record_id, user_id, update_data)
                    if updated_record:
                        st.success(f"Record ID {selected_record_id} updated successfully!")
                        logger.info(f"User {user_id} updated record {selected_record_id}.")
                        st.session_state["current_main_page"] = "View Records" # Stay on this page
                        st.rerun()
                    else:
                        st.error("Failed to update record. Check if the record exists and belongs to you.")
                except Exception as e:
                    st.error(f"Error updating record: {e}")
                    logger.error(f"Error updating record {selected_record_id} for user {user_id}: {e}")
                finally:
                    db_update.close()

            if delete_button_trigger:
                # Add a confirmation step for deletion
                st.warning(f"Are you absolutely sure you want to delete Record ID {selected_record_id}? This action cannot be undone.")
                col_confirm1, col_confirm2 = st.columns(2)
                with col_confirm1:
                    if st.button("Yes, Delete Permanently", key=f"confirm_delete_yes_{selected_record_id}"):
                        db_gen_delete = get_db()
                        db_delete = next(db_gen_delete)
                        try:
                            if delete_receipt(db_delete, selected_record_id, user_id):
                                st.success(f"Record ID {selected_record_id} deleted successfully.")
                                logger.info(f"User {user_id} deleted record {selected_record_id}.")
                                st.session_state["current_main_page"] = "View Records" # Stay on this page
                                st.rerun()
                            else:
                                st.error("Failed to delete record. Check if the record exists and belongs to you.")
                        except Exception as e:
                            st.error(f"Error deleting record: {e}")
                            logger.error(f"Error deleting record {selected_record_id} for user {user_id}: {e}")
                        finally:
                            db_delete.close()
                with col_confirm2:
                    if st.button("No, Cancel Deletion", key=f"confirm_delete_no_{selected_record_id}"):
                        st.info("Deletion cancelled.")
                        st.rerun() # Refresh to clear confirmation prompt

    else:
        st.info("Select a record ID above to enable manual correction or deletion.")


    st.markdown("---")

    # --- Export Data ---
    st.header("Export Your Data")
    st.markdown("Download your filtered transaction records in CSV or JSON format.")

    if not df.empty:
        csv_data = convert_df_to_csv(df)
        json_data = convert_df_to_json(df)

        col_export1, col_export2 = st.columns(2)
        with col_export1:
            st.download_button(
                label="Download as CSV",
                data=csv_data,
                file_name=f"receipt_records_{user_id}_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="Download all current filtered records as a CSV file."
            )
        with col_export2:
            st.download_button(
                label="Download as JSON",
                data=json_data,
                file_name=f"receipt_records_{user_id}_{date.today().strftime('%Y%m%d')}.json",
                mime="application/json",
                help="Download all current filtered records as a JSON file."
            )
    else:
        st.warning("No records to export. Please upload some data first.")

import streamlit as st
import pandas as pd
from ui.auth_manager import AuthManager
from database.crud import get_receipts_by_user, get_all_vendors, get_all_categories
from database.database import get_db
from processing.aggregation import calculate_expenditure_summary, get_vendor_frequency, get_monthly_spend_trend
from ui.plots import plot_pie_chart, plot_bar_chart, plot_line_chart
from ui.components import display_info_card
from datetime import date
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_dashboard_page():
    auth_manager = AuthManager()
    auth_manager.require_login() # Ensure user is logged in

    user_id = auth_manager.get_current_user_id()
    username = auth_manager.get_current_username()

    st.title(f"📊 Dashboard - {username}'s Spending Insights")
    st.markdown("Explore your financial trends and summaries.")

    db_gen = get_db()
    db = next(db_gen)
    receipts_db_objects = get_receipts_by_user(db, user_id, limit=None) # Get all receipts for dashboard
    vendors_map = {v.id: v.name for v in get_all_vendors(db)}
    categories_map = {c.id: c.name for c in get_all_categories(db)}
    db.close()

    if not receipts_db_objects:
        st.info("No receipts uploaded yet. Please upload some to see insights!")
        st.subheader("How to get started?")
        st.markdown("Navigate to the **'Upload Receipt'** page from the sidebar and start digitizing your expenses!")
        return

    # Convert SQLAlchemy objects to pandas DataFrame for easier processing
    receipt_dicts = []
    for r in receipts_db_objects:
        receipt_dicts.append({
            "id": r.id,
            "vendor_name": vendors_map.get(r.vendor_id, "Unknown Vendor"),
            "transaction_date": r.transaction_date,
            "amount": r.amount,
            "currency": r.currency,
            "category_name": categories_map.get(r.category_id, "Uncategorized"),
            "original_filename": r.original_filename,
            "upload_date": r.upload_date
        })
    df = pd.DataFrame(receipt_dicts)

    # Convert transaction_date to datetime for time-series analysis if it's not already
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    # --- Summary Statistics ---
    st.header("Overall Spending Summary")
    total_spend, mean_spend, median_spend, mode_spend = calculate_expenditure_summary(df, 'amount')

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        display_info_card("Total Spend", f"{total_spend:.2f} {df['currency'].iloc[0] if not df.empty else ''}", "💰") # Use first currency found
    with col2:
        display_info_card("Average Spend", f"{mean_spend:.2f} {df['currency'].iloc[0] if not df.empty else ''}", "📈")
    with col3:
        display_info_card("Median Spend", f"{median_spend:.2f} {df['currency'].iloc[0] if not df.empty else ''}", "📊")
    with col4:
        display_info_card("Most Common Spend", f"{mode_spend[0]:.2f} {df['currency'].iloc[0] if mode_spend else ''}" if mode_spend else "N/A", "🎯")

    # --- Visualizations ---
    st.header("Detailed Spending Visualizations")

    # Vendor Frequency
    st.subheader("Top 10 Vendors")
    vendor_freq_df = get_vendor_frequency(df).head(10) # Show top 10
    if not vendor_freq_df.empty:
        fig_vendor = plot_bar_chart(vendor_freq_df, 'vendor_name', 'count', 'Spending Distribution by Vendor',
                                    hover_data=['count'])
        st.plotly_chart(fig_vendor, use_container_width=True)
    else:
        st.info("No vendor data to display.")

    # Category Distribution
    st.subheader("Spending by Category")
    category_spend_df = df.groupby('category_name')['amount'].sum().reset_index().sort_values(by='amount', ascending=False)
    if not category_spend_df.empty:
        fig_category = plot_pie_chart(category_spend_df, 'category_name', 'amount', 'Spending Distribution by Category',
                                      hover_data=['amount'])
        st.plotly_chart(fig_category, use_container_width=True)
    else:
        st.info("No category data to display.")

    # Monthly Spend Trend with Rolling Average
    st.subheader("Monthly Spending Trend")
    # Define a rolling window for monthly trend (e.g., 3 months)
    rolling_window_option = st.slider("Select Rolling Average Window (Months)", min_value=1, max_value=6, value=3, step=1,
                                     help="Calculate the average spend over the selected number of past months.")

    monthly_trend_df = get_monthly_spend_trend(df, 'transaction_date', 'amount', rolling_window=rolling_window_option)
    if not monthly_trend_df.empty:
        fig_monthly_trend = plot_line_chart(monthly_trend_df, 'month', 'total_amount', 'Monthly Expenditure Trend',
                                            y_secondary_col='rolling_avg' if 'rolling_avg' in monthly_trend_df.columns else None,
                                            hover_data={'total_amount': ':.2f', 'rolling_avg': ':.2f'}) # Format hover
        st.plotly_chart(fig_monthly_trend, use_container_width=True)
    else:
        st.info("No monthly trend data to display.")

    st.header("Raw Data View")
    st.markdown("<p style='font-family: \"Roboto\", sans-serif;'>For a detailed look at your transactions, navigate to the 'View Records' page.</p>", unsafe_allow_html=True)
    if st.button("Go to View Records"):
        # Corrected: Set the session state variable that controls the radio button's *initial value*
        # in the *next* rerun, then force a rerun.
        st.session_state["current_main_page"] = "View Records" # This is the variable app.py uses
        st.rerun()

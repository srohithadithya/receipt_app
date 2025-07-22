import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import date, datetime # Already imported, good!

def display_records_table(df: pd.DataFrame, key: str = "records_table"):
    """
    Displays a DataFrame as an interactive table in Streamlit.
    Adds options for column configuration and editing (for manual correction).

    :param df: Pandas DataFrame to display.
    :param key: A unique key for the Streamlit component.
    """
    if df.empty:
        st.info("No records to display.")
        return

    # Convert date/datetime objects to strings for consistent display in st.dataframe editing
    df_display = df.copy()
    for col in df_display.columns:
        # Check if column is datetime already (Pandas' native datetime64)
        if pd.api.types.is_datetime64_any_dtype(df_display[col]):
            # If it's already datetime64, just format it
            df_display[col] = df_display[col].dt.strftime('%Y-%m-%d')
        # Check if it's an object dtype column that *should* contain dates/datetimes
        elif pd.api.types.is_object_dtype(df_display[col]) and not df_display[col].dropna().empty:
            # Attempt to convert to datetime. Coerce errors will turn unparseable values to NaT (Not a Time).
            # We then check if the conversion was successful for at least some values before formatting.
            temp_series = pd.to_datetime(df_display[col], errors='coerce')
            
            # Check if the conversion resulted in a datetime series AND if it originally contained date/datetime objects
            if pd.api.types.is_datetime64_any_dtype(temp_series) and \
               temp_series.dropna().apply(lambda x: isinstance(x.to_pydatetime().date(), (date, datetime))).all():
                df_display[col] = temp_series.dt.strftime('%Y-%m-%d').fillna('') # Fill NaN dates with empty string
            elif all(isinstance(x, date) for x in df_display[col].dropna()): # Specifically for pure Python date objects
                # Convert Python date objects to strings directly if not convertible to datetime64 by pd.to_datetime
                df_display[col] = df_display[col].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, date) else x)

        elif pd.api.types.is_integer_dtype(df_display[col]): # Ensure integers are not float in editing
             df_display[col] = df_display[col].astype(str)


    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        key=key,
        # Streamlit's data_editor supports editing
        # For more controlled editing, you'd handle specific columns here
        # E.g., column_config={ "amount": st.column_config.NumberColumn("Amount", format="%.2f") }
    )
    st.caption(f"Displaying {len(df)} records.")

def create_sidebar_logo(logo_path: str = "assets/images/logo.png"):
    """
    Displays the application logo in the sidebar.
    :param logo_path: Path to the logo image file.
    """
    try:
        st.sidebar.image(logo_path, use_column_width=True)
    except FileNotFoundError:
        st.sidebar.warning("Logo file not found. Please check path: " + logo_path)
    except Exception as e:
        st.sidebar.error(f"Error loading logo: {e}")


def display_info_card(title: str, value: Any, icon: str = ""):
    """
    Displays a stylized info card with a title, value, and optional icon.
    """
    st.markdown(f"""
    <div style="
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    ">
        <h3 style="color: #4CAF50; margin-bottom: 5px;">{icon} {title}</h3>
        <p style="font-size: 2em; font-weight: bold; color: #303030;">{value}</p>
    </div>
    """, unsafe_allow_html=True)

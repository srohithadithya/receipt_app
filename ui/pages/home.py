import streamlit as st
import time # For potential subtle pauses if needed in future, though not used for direct animation here

def show_home_page():
    col_logo, col_title = st.columns([0.2, 0.8]) # Adjust ratio as needed for your logo size

    with col_logo:
        # Ensure the logo path is correct and the image is valid PNG
        st.image("assets/images/logo.png", width=100) # Smaller width for inline display

    with col_title:
        # Using markdown with custom class for the title itself
        st.markdown('<h1 class="welcome-header-title">Welcome to Receipt & Bill Tracker!</h1>', unsafe_allow_html=True)

    # Injecting CSS specifically for the home page header to align content properly
    st.markdown("""
        <style>
        .welcome-header-title {
            margin-top: 0; /* Remove default top margin */
            margin-bottom: 0; /* Remove default bottom margin */
            padding-top: 10px; /* Adjust vertical alignment with logo */
            color: #2E8B57; /* Consistent strong green */
            font-size: 3em; /* Large font size */
            font-family: 'Montserrat', sans-serif; /* Consistent header font */
        }
        /* Override default Streamlit image block padding/margin for better alignment */
        .stImage {
            margin-top: 0;
            margin-bottom: 0;
            padding-top: 0;
            padding-bottom: 0;
        }
        /* To remove yellow line, ensure no caption is used with st.image */
        </style>
    """, unsafe_allow_html=True)


    st.markdown("""
    <div style="background-color: #e8f5e9; padding: 25px; border-radius: 10px; margin-top: 20px; margin-bottom: 30px; border-left: 5px solid #4CAF50;">
        <h2 style="color: #4CAF50; margin-top: 0px; font-family: 'Montserrat', sans-serif;">Your Personal Finance Co-Pilot</h2>
        <p style="font-size: 1.1em; font-family: 'Roboto', sans-serif;">
            Tired of manually tracking your expenses? Lost in a sea of paper receipts?
            The **Receipt & Bill Tracker** revolutionizes how you manage your money.
            Simply upload your receipts and bills, and let our intelligent system do the rest!
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.header("What Makes Us Unique? 🤔")

    col_feature1, col_feature2 = st.columns(2) # Columns for feature sections

    with col_feature1:
        st.subheader("Automated & Intelligent Data Extraction")
        st.markdown("""
        <ul style="font-family: 'Roboto', sans-serif; font-size: 1.05em; line-height: 1.8;">
            <li><b>Smart Parsing</b>: Our core engine uses advanced rule-based logic and cutting-edge <b>OCR (Optical Character Recognition)</b> to automatically pull out key details like <b>vendor, date, and amount</b> from diverse documents (images, PDFs, text files).</li>
            <li><b>Multi-Format Support</b>: Whether it's a blurry photo, a crisp PDF, or a simple text file, we handle it all.</li>
            <li><b>Multi-Currency & Language (Bonus!)</b>: Detects different currencies and can even process receipts in multiple languages, making it truly global.</li>
        </ul>
        """, unsafe_allow_html=True)
        st.image("assets/images/ai_chart_summary.png", use_column_width=True)

    with col_feature2:
        st.subheader("Deep Dive into Your Spending Habits")
        st.markdown("""
        <ul style="font-family: 'Roboto', sans-serif; font-size: 1.05em; line-height: 1.8;">
            <li><b>Powerful Analytics</b>: Beyond simple tracking, we apply core algorithms for <b>searching, sorting, and aggregating</b> your financial data.</li>
            <li><b>Visual Insights</b>: Understand your spending with interactive dashboards featuring <b>bar charts, pie charts, and time-series graphs</b> showing trends like total spend, top vendors, and monthly expenditure.</li>
            <li><b>Data Integrity</b>: Robust <b>validation mechanisms</b> ensure that the extracted data is accurate and reliable. You can even <b>manually correct fields</b> if needed!</li>
            <li><b>Secure & Private</b>: Your financial data is stored securely in a lightweight, ACID-compliant database, accessible only to you through a protected login system.</li>
        </ul>
        """, unsafe_allow_html=True)
        st.image("assets/images/ai_finance_bg.png", use_column_width=True)


    st.subheader("Ready to Take Control of Your Finances?")
    st.markdown("<p style='font-family: \"Roboto\", sans-serif; font-size: 1.1em;'>Join us today and transform your financial management!</p>", unsafe_allow_html=True)

    # --- Button Alignment and Grouping ---
    # Using columns to align buttons side-by-side for "Join Us Today" section
    col_signup_btn, col_login_btn = st.columns(2) # Two equal-width columns for buttons

    with col_signup_btn:
        # Use a distinct key for each button to avoid Streamlit warnings
        if st.button("🚀 Get Started (Sign Up)", key="home_signup_btn"):
            st.session_state["auth_nav_radio_selected"] = "Signup" # Update session state for sidebar radio
            st.rerun() # Force a rerun to navigate

    with col_login_btn:
        if st.button("➡️ Already have an account? (Login)", key="home_login_btn"):
            st.session_state["auth_nav_radio_selected"] = "Login" # Update session state for sidebar radio
            st.rerun() # Force a rerun to navigate

    # Optional: Small footer
    st.markdown("<br><p style='text-align: center; color: #888; font-family: \"Roboto\", sans-serif;'>© 2025 Receipt & Bill Tracker. All rights reserved.</p>", unsafe_allow_html=True)

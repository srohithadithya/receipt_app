import streamlit as st
import time # Not for heavy animations, but can be used for subtle pauses if desired

def show_home_page():
    # --- Logo and Title Side-by-Side ---
    # Using markdown with custom CSS class for horizontal alignment and styling
    st.markdown("""
    <div class="welcome-header">
        <img src="assets/images/logo.png" alt="Receipt Tracker Logo",width=150>
        <h1>Welcome to Receipt & Bill Tracker!</h1>
    </div>
    """, unsafe_allow_html=True)


    st.markdown("""
    <div style="background-color: #e8f5e9; padding: 25px; border-radius: 10px; margin-bottom: 30px; border-left: 5px solid #4CAF50;">
        <h2 style="color: #4CAF50; margin-top: 0px; font-family: 'Montserrat', sans-serif;">Your Personal Finance Co-Pilot</h2>
        <p style="font-size: 1.1em; font-family: 'Roboto', sans-serif;">
            Tired of manually tracking your expenses? Lost in a sea of paper receipts?
            The **Receipt & Bill Tracker** revolutionizes how you manage your money.
            Simply upload your receipts and bills, and let our intelligent system do the rest!
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.header("What Makes Us Unique? 🤔")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Automated & Intelligent Data Extraction")
        st.markdown("""
        * <p style="font-family: 'Roboto', sans-serif;"><b>Smart Parsing</b>: Our core engine uses advanced rule-based logic and cutting-edge <b>OCR (Optical Character Recognition)</b> to automatically pull out key details like <b>vendor, date, and amount</b> from diverse documents (images, PDFs, text files).</p>
        * <p style="font-family: 'Roboto', sans-serif;"><b>Multi-Format Support</b>: Whether it's a blurry photo, a crisp PDF, or a simple text file, we handle it all.</p>
        * <p style="font-family: 'Roboto', sans-serif;"><b>Multi-Currency & Language (Bonus!)</b>: Detects different currencies and can even process receipts in multiple languages, making it truly global.</p>
        """, unsafe_allow_html=True)
        st.image("assets/images/ai_chart_summary.png", use_column_width=True, caption="AI-powered insights at your fingertips")

    with col2:
        st.subheader("Deep Dive into Your Spending Habits")
        st.markdown("""
        * <p style="font-family: 'Roboto', sans-serif;"><b>Powerful Analytics</b>: Beyond simple tracking, we apply core algorithms for <b>searching, sorting, and aggregating</b> your financial data.</p>
        * <p style="font-family: 'Roboto', sans-serif;"><b>Visual Insights</b>: Understand your spending with interactive dashboards featuring <b>bar charts, pie charts, and time-series graphs</b> showing trends like total spend, top vendors, and monthly expenditure.</p>
        * <p style="font-family: 'Roboto', sans-serif;"><b>Data Integrity</b>: Robust <b>validation mechanisms</b> ensure that the extracted data is accurate and reliable. You can even <b>manually correct fields</b> if needed!</p>
        * <p style="font-family: 'Roboto', sans-serif;"><b>Secure & Private</b>: Your financial data is stored securely in a lightweight, ACID-compliant database, accessible only to you through a protected login system.</p>
        """, unsafe_allow_html=True)
        st.image("assets/images/ai_finance_bg.png", use_column_width=True, caption="Intelligent financial management")

    st.markdown("---")

    st.subheader("Ready to Take Control of Your Finances?")
    st.markdown("<p style='font-family: \"Roboto\", sans-serif; font-size: 1.1em;'>Join us today and transform your financial management!</p>", unsafe_allow_html=True)

    # --- Button Alignment and Grouping ---
    # Using columns to align buttons side-by-side naturally
    col_signup_btn, col_login_btn = st.columns(2) # Two columns for two buttons

    with col_signup_btn:
        if st.button("🚀 Get Started (Sign Up)", key="home_signup_btn"):
            st.session_state["auth_nav_radio_selected"] = "Signup" # Update session state for sidebar radio
            st.rerun()
    with col_login_btn:
        if st.button("➡️ Already have an account? (Login)", key="home_login_btn"):
            st.session_state["auth_nav_radio_selected"] = "Login" # Update session state for sidebar radio
            st.rerun()

    # Optional: Small footer
    st.markdown("<br><p style='text-align: center; color: #888;'>© 2025 Receipt & Bill Tracker. All rights reserved.</p>", unsafe_allow_html=True)

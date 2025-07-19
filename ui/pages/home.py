import streamlit as st
import time # For potential loading effects or pauses

def show_home_page():
    st.image("assets/images/logo.png", width=150) # Adjust path as needed
    st.title("💸 Welcome to Receipt & Bill Tracker!")

    st.markdown("""
    <div style="background-color: #e8f5e9; padding: 25px; border-radius: 10px; margin-bottom: 30px; border-left: 5px solid #4CAF50;">
        <h2 style="color: #4CAF50; margin-top: 0px;">Your Personal Finance Co-Pilot</h2>
        <p style="font-size: 1.1em;">
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
        * **Smart Parsing**: Our core engine uses advanced rule-based logic and cutting-edge **OCR (Optical Character Recognition)** to automatically pull out key details like **vendor, date, and amount** from diverse documents (images, PDFs, text files).
        * **Multi-Format Support**: Whether it's a blurry photo, a crisp PDF, or a simple text file, we handle it all.
        * **Multi-Currency & Language (Bonus!)**: Detects different currencies and can even process receipts in multiple languages, making it truly global.
        """)
        st.image("assets/images/ai_chart_summary.png", use_column_width=True, caption="AI-powered insights at your fingertips") # Placeholder for AI pic

    with col2:
        st.subheader("Deep Dive into Your Spending Habits")
        st.markdown("""
        * **Powerful Analytics**: Beyond simple tracking, we apply core algorithms for **searching, sorting, and aggregating** your financial data.
        * **Visual Insights**: Understand your spending with interactive dashboards featuring **bar charts, pie charts, and time-series graphs** showing trends like total spend, top vendors, and monthly expenditure.
        * **Data Integrity**: Robust **validation mechanisms** ensure that the extracted data is accurate and reliable. You can even **manually correct fields** if needed!
        * **Secure & Private**: Your financial data is stored securely in a lightweight, ACID-compliant database, accessible only to you through a protected login system.
        """)
        st.image("assets/images/ai_finance_bg.png", use_column_width=True, caption="Intelligent financial management") # Placeholder for AI pic

    st.markdown("---")

    st.subheader("Ready to Take Control of Your Finances?")
    st.markdown("Join us today and transform your financial management!")

    col_btn1, col_btn2, col_btn3 = st.columns([1,1,4])
    with col_btn1:
        if st.button("🚀 Get Started (Sign Up)", key="home_signup_btn"):
            st.session_state["auth_nav"] = "Signup" # Redirect to Signup via sidebar radio
            st.rerun()
    with col_btn2:
        if st.button("➡️ Already have an account? (Login)", key="home_login_btn"):
            st.session_state["auth_nav"] = "Login" # Redirect to Login via sidebar radio
            st.rerun()
    with col_btn3:
        pass # Empty column for spacing
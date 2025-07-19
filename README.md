# **Receipt & Bill Tracker**

## **Table of Contents**

1.  **[Introduction](#1-introduction)**
2.  **[Features](#2-features)**
    * **[Core Functionality](#21-core-functionality)**
    * **[Advanced Capabilities](#22-advanced-capabilities)**
    * **[Authentication & Security](#23-authentication--security)**
3.  **[Technical Architecture](#3-technical-architecture)**
4.  **[Setup & Installation](#4-setup--installation)**
    * **[Prerequisites](#41-prerequisites)**
    * **[Installation Steps](#42-installation-steps)**
    * **[Running the Application](#43-running-the-application)**
5.  **[Usage Guide](#5-usage-guide)**
    * **[Registration & Login](#51-registration--login)**
    * **[Uploading Receipts](#52-uploading-receipts)**
    * **[Viewing & Managing Records](#53-viewing--managing-records)**
    * **[Exploring Insights](#54-exploring-insights)**
    * **[Manual Correction](#55-manual-correction)**
    * **[Exporting Data](#56-exporting-data)**
6.  **[Design Choices & Assumptions](#6-design-choices--assumptions)**
7.  **[Limitations](#7-limitations)**
8.  **[Future Enhancements](#8-future-enhancements)**
9.  **[Contributing](#9-contributing)**
10. **[License](#10-license)**

---

## **1. Introduction**

**Welcome to the Receipt & Bill Tracker**, an **innovative full-stack mini-application** designed to **streamline the daunting task of managing your personal finances**. This tool **empowers users to effortlessly upload receipts and bills** (e.g., electricity, internet, groceries), **automatically extract crucial financial data**, and **transform raw expenditures into insightful visualizations and actionable trends**. Built with a focus on **robust backend algorithms and a user-friendly interface**, it's your go-to solution for **gaining unparalleled clarity into your spending habits**.

## **2. Features**

### **2.1. Core Functionality**

* [cite_start]**Diverse Data Ingestion**: **Seamlessly handles various file formats** including **.jpg, .png, .pdf, and .txt**[cite: 1].
* **Intelligent Data Parsing**: **Extracts key structured data fields** including:
    * [cite_start]**Vendor / Biller** [cite: 1]
    * [cite_start]**Date of Transaction / Billing Period** [cite: 1]
    * [cite_start]**Amount** [cite: 1]
    * [cite_start]**Category**  [cite: 1]
    * [cite_start]**Utilizes rule-based logic and/or Optical Character Recognition (OCR)** for precision[cite: 1].
* [cite_start]**Secure Data Storage**: **Persists all extracted data in a normalized form within a lightweight SQLite relational database**, **ensuring ACID compliance and optimized search performance through indexing**[cite: 1].
* **Advanced Search Capabilities**: **Offers keyword-, range-, and pattern-based search mechanisms**, leveraging efficient string matching and comparison operators. [cite_start]**Supports both linear search and hashed indexing for optimization**[cite: 1].
* [cite_start]**Flexible Sorting**: **Enables sorting of records based on numerical (e.g., amount) and categorical (e.g., vendor, category) fields** [cite: 1] [cite_start]using efficient in-memory sorting techniques (e.g., Timsort, custom quicksort/mergesort)[cite: 1].
* **Powerful Aggregation Functions**: **Computes vital statistical aggregates** to summarize your spending:
    * [cite_start]**Sum, Mean, Median, Mode of expenditure** [cite: 1]
    * [cite_start]**Frequency distributions (histograms) of vendor occurrences** [cite: 1]
    * [cite_start]**Time-series aggregations** (e.g., monthly spend trends using sliding windows) [cite: 1]

### **2.2. Advanced Capabilities**

* [cite_start]**Interactive Statistical Visualizations**: **Presents categorical distributions via intuitive bar and pie charts**, offering visual representations of spending across vendors or categories[cite: 1].
* [cite_start]**Dynamic Time-Series Graphs**: **Visualizes expenditure trends over time using line charts**, with options for moving averages or deltas to highlight patterns[cite: 1].
* [cite_start]**Robust Validation & Error Handling**: **Implements formal validation rules on file types, parsing logic, and data schemas** [cite: 1][cite_start], **providing informative feedback without halting system operations through comprehensive exception handling**[cite: 1].

### **2.3. Authentication & Security**

* **User Registration**: **Allows new users to securely sign up for an account**.
* **Secure Login**: **Provides a dedicated login interface for returning users**.
* **Password Hashing**: **Employs robust cryptographic hashing (bcrypt via `passlib`) to store user passwords securely**, ensuring sensitive information is never stored in plaintext.
* **Session Management**: **Maintains user session state for a seamless and secure authenticated experience**.

### **2.4. Bonus Features (Stretch Goals Implemented)**

* [cite_start]**Manual Data Correction**: **Empowers users to manually edit and correct parsed fields via the UI**[cite: 1].
* [cite_start]**Data Export**: **Facilitates easy export of summaries as .csv or .json** [cite: 1] for external analysis or record-keeping.
* [cite_start]**Currency Detection**: **Automatically detects or supports multi-currency handling**[cite: 1].
* [cite_start]**Multi-language Processing**: **Capability to process multi-language receipts/bills**[cite: 1].

## **3. Technical Architecture**

**The application follows a modular, full-stack architecture**, primarily leveraging Python for both its backend processing and interactive frontend:

* **Frontend (UI Layer)**: Developed using **Streamlit**, enabling **rapid development of an interactive and visually appealing web interface entirely in Python**.
* **Backend (Processing Layer)**:
    * [cite_start]**Data Ingestion & Validation**: Handled by **Pillow** for images, **PyPDF2** for PDFs, and **Pydantic** for robust data validation[cite: 1].
    * **Data Parsing**: Utilizes **pytesseract** for OCR integration (requires system-wide Tesseract installation) and custom rule-based logic. **OpenCV-Python** assists in image pre-processing for OCR.
    * [cite_start]**Algorithmic Core**: **Native Python implementations for search, sort, and aggregation algorithms**[cite: 1]. **NumPy** and **Pandas** are used for advanced numerical computations and time-series analysis.
    * **User Authentication**: Utilizes **passlib[bcrypt]** for secure password hashing and verification.
* [cite_start]**Database Layer**: A lightweight **SQLite relational database** serves as the persistent storage, accessed and managed efficiently via **SQLAlchemy ORM**[cite: 1].

**This design ensures clear separation of concerns, high maintainability, and extensibility**.

receipt_app/
├── .streamlit/ # Streamlit configuration
│   └── config.toml
├── data/ # Storage for uploaded files
│   └── raw_receipts/           # Original uploaded files
│   └── processed_data/         # Interim processed data if needed
├── database/ # SQLAlchemy models and CRUD operations
│   ├── init.py
│   ├── database.py # DB connection setup
│   ├── models.py # DB schema (User, Receipt, Vendor, Category)
│   └── crud.py # DB interactions
├── processing/ # Core data handling logic
│   ├── init.py
│   ├── validation.py # Pydantic models & file validation
│   ├── ingestion.py # File I/O
│   ├── parsing.py # Data extraction (OCR, rules)
│   ├── ocr_utils.py # OCR specific helpers
│   ├── algorithms/
│   │   ├── init.py
│   │   ├── search.py # Search algorithms
│   │   └── sort.py # Sorting algorithms
│   └── aggregation.py # Statistical computations
├── ui/ # Streamlit UI components
│   ├── init.py
│   ├── components.py # Reusable UI widgets
│   ├── plots.py # Visualization functions
│   ├── pages/ # Multi-page application structure
│   │   ├── auth/ # Login and Signup pages
│   │   │   ├── init.py
│   │   │   ├── login.py # Login page UI and logic
│   │   │   └── signup.py # Signup page UI and logic
│   │   ├── dashboard.py # Main insights view
│   │   ├── upload.py # Receipt upload page
│   │   └── records.py # Individual record view & manual correction
│   └── auth_manager.py # Streamlit session state for auth
├── utils/ # General utilities and security
│   ├── init.py
│   ├── helpers.py # Date, currency, export utilities
│   ├── security.py # Password hashing & verification
│   └── errors.py # Custom exceptions
├── tests/ # Unit and integration tests
│   ├── test_database.py
│   ├── test_processing.py
│   ├── test_ui.py
│   └── test_auth.py # Tests for authentication logic
├── .gitignore # Git ignore file
├── app.py # Main Streamlit application entry point
├── requirements.txt # Python dependency list
└── README.md # Project documentation

## **4. Setup & Installation**

**Follow these steps to get the Receipt & Bill Tracker up and running on your local machine.**

### **4.1. Prerequisites**

* **Python 3.12.0** (or higher recommended)
* **Tesseract OCR Engine**: This is a system-level dependency.
    * **Windows**: **Download and install from the [Tesseract OCR GitHub](https://github.com/UB-Mannheim/tesseract/wiki)**. **Ensure you add Tesseract to your system's PATH variable during installation, or note its installation path**.
    * **macOS (using Homebrew)**:
        ```bash
        brew install tesseract
        ```
    * **Linux (Debian/Ubuntu)**:
        ```bash
        sudo apt-get update
        sudo apt-get install tesseract-ocr
        ```

### **4.2. Installation Steps**

1.  **Clone the Repository**:
    ```bash
    git clone [https://github.com/your-username/receipt_app.git](https://github.com/your-username/receipt_app.git)
    cd receipt_app
    ```

2.  **Create a Virtual Environment** (Highly Recommended):
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment**:
    * **Windows**:
        ```bash
        .\venv\Scripts\activate
        ```
    * **macOS / Linux**:
        ```bash
        source venv/bin/activate
        ```
    (**You should see `(venv)` at the beginning of your terminal prompt**.)

4.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt

    *If `requirements.txt` is not yet generated, you can install manually:*
    ```bash
    pip install Pillow PyPDF2 pydantic pytesseract opencv-python SQLAlchemy numpy pandas streamlit matplotlib seaborn "passlib[bcrypt]"
    ```

5.  **Initialize the Database**:
    **The application will automatically create the `receipt_app.db` SQLite database and its tables on first run**, based on the SQLAlchemy models defined in `database/models.py`.

### **4.3. Running the Application**

1.  **Ensure your virtual environment is active**.
2.  **Navigate to the root directory** of the project (`receipt_app/`).
3.  **Run the Streamlit application**:
    ```bash
    streamlit run app.py
    ```
    **This command will open the application in your default web browser (usually `http://localhost:8501`)**.

## **5. Usage Guide**

### **5.1. Registration & Login**

* **Upon first access, you will be redirected to the Signup page**. **Create your account with a unique username and a strong password**.
* **After successful registration, navigate to the Login page to access the application's features**.
* **Your session will be maintained, allowing you to seamlessly navigate the application**.

### **5.2. Uploading Receipts**

* **Go to the "Upload" page in the navigation**.
* **Drag and drop or browse to select your receipt/bill files** (`.jpg`, `.png`, `.pdf`, `.txt`).
* **The application will automatically process the files, extract data, and store it**.

### **5.3. Viewing & Managing Records**

* **The "Records" page displays a tabular view of all your uploaded and parsed receipts**.
* **You can sort records by various fields** (e.g., date, amount, vendor) to easily find specific transactions.

### **5.4. Exploring Insights**

* **The "Dashboard" page provides a comprehensive overview of your spending**.
* **View statistical summaries** (total spend, average, etc.) and **interactive charts illustrating vendor frequency, category distribution, and monthly spending trends**.

### **5.5. Manual Correction**

* **On the "Records" page, you can select individual entries to manually correct any parsed fields** (e.g., if OCR misread an amount or date).

### **5.6. Exporting Data**

* **Summarized data from your dashboard or detailed records can be exported to .csv or .json formats** for external analysis or record-keeping.

## **6. Design Choices & Assumptions**

* [cite_start]**Pythonic Approach**: **Emphasis on leveraging native Python data structures and algorithmic thinking for core logic**[cite: 1].
* **Streamlit for Rapid UI**: **Chosen for its ability to build interactive web applications purely in Python**, reducing development complexity and overhead.
* [cite_start]**SQLite for Lightweight Persistence**: **Ideal for a mini-application due to its file-based nature, zero-configuration, and direct integration with Python**[cite: 1].
* **SQLAlchemy ORM**: **Provides an abstraction layer over SQL, enhancing development speed and maintainability of database interactions**.
* [cite_start]**Pydantic for Data Integrity**: **Ensures robust validation of incoming and extracted data**, maintaining high data quality[cite: 1].
* **Modular Codebase**: **Organized into logical directories** (`processing`, `database`, `ui`, `utils`) to promote code reusability, testability, and maintainability.
* [cite_start]**Explicit Error Handling**: **Designed to provide informative user feedback without crashing the application**[cite: 1].
* **Tesseract OCR**: **Chosen for its open-source nature and robust OCR capabilities for varied document types**.
* **Single-User Focus**: **While authentication is implemented, the primary analytics and data views are tailored for an individual user's financial data**. **Multi-user data isolation is inherent through separate user accounts**.

## **7. Limitations**

* **OCR Accuracy**: **While robust, OCR accuracy can vary significantly based on receipt quality** (e.g., crumpled, faded, handwritten, complex layouts). **Manual correction is provided to mitigate this**.
* **Rule-Based Parsing Complexity**: **Rule-based extraction might struggle with highly diverse or unstructured receipt layouts that deviate from expected patterns**.
* **Scalability**: **SQLite is suitable for a personal application but might not be optimal for very large datasets or high concurrency requirements in an enterprise setting**.
* **Language Support**: **While multi-language processing is a bonus feature, its effectiveness depends on the OCR engine's training data and the complexity of the language scripts**.
* **Currency Detection**: **Automatic currency detection may have limitations with ambiguous symbols or when multiple currencies are present without clear indicators**.

## **8. Future Enhancements**

* **Machine Learning for Parsing**: **Implement ML models** (e.g., Named Entity Recognition) for more robust and adaptable data extraction from receipts, **reducing reliance on strict rule-based parsing**.
* **Cloud Deployment Options**: **Provide Dockerization or cloud deployment scripts** (e.g., AWS, Azure, GCP) for easier scaling and accessibility.
* **Advanced Analytics**: **Incorporate budget tracking, anomaly detection in spending, or predictive analytics**.
* **Integration with Financial APIs**: **Connect to banking APIs (with user consent) for automated transaction reconciliation**.
* **Enhanced Category Mapping**: **Allow users to define custom categories and rules for auto-categorization**.
* **Mobile Responsiveness**: **Improve UI responsiveness for a better experience on mobile devices**.
* **User Roles & Permissions**: **If expanding to a collaborative environment, implement granular user roles**.

## **9. Contributing**

**We welcome contributions to enhance the Receipt & Bill Tracker! If you're interested in contributing, please:**

1.  **Fork the repository**.
2.  **Create a new branch for your feature or bug fix**.
3.  **Implement your changes and ensure tests pass**.
4.  **Submit a pull request with a clear description of your changes**.
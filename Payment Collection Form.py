import streamlit as st
import json
import os
import uuid
import base64
import zipfile
import io
import pandas as pd
from datetime import datetime
from pathlib import Path
import hashlib

# Page configuration
st.set_page_config(
    page_title="Student Payment System",
    page_icon="🎓",
    layout="wide"
)

# File paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
STUDENTS_FILE = DATA_DIR / "students.json"
ADMIN_FILE = DATA_DIR / "admin.json"
PAYMENT_FILE = DATA_DIR / "payments.json"
INSTRUCTIONS_FILE = DATA_DIR / "instructions.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Initialize data files
def init_files():
    default_data = {
        "students": [],
        "admin": {
            "username": "admin",
            "password": "admin123",  # Will be hashed
            "payment_amount": 5000,
            "payment_accounts": [{"bank": "Bank Name", "account": "1234567890", "name": "Account Holder"}],
            "short_url_code": str(uuid.uuid4())[:8],
            "base_url": "http://localhost:8501",  # New: Base URL field
            "instructions": "Default instructions for students.",
            "additional_instructions": "Please make payment to the given account and upload screenshot.",
            "form_published": True,
            "contact_email": "admin@example.com",
            "contact_phone": "+91 9876543210",
            "tab_visibility": {
                "account_details": True,
                "submit_payment": True,
                "payment_status": True,
                "student_list": True,
                "instructions": True
            }
        },
        "payments": [],
        "instructions": "Default instructions will appear here."
    }
    
    # Initialize students.json
    if not STUDENTS_FILE.exists():
        with open(STUDENTS_FILE, 'w') as f:
            json.dump(default_data["students"], f, indent=2)
    
    # Initialize admin.json with hashed password
    if not ADMIN_FILE.exists():
        admin_data = default_data["admin"]
        admin_data["password"] = hash_password(admin_data["password"])
        with open(ADMIN_FILE, 'w') as f:
            json.dump(admin_data, f, indent=2)
    
    # Initialize payments.json
    if not PAYMENT_FILE.exists():
        with open(PAYMENT_FILE, 'w') as f:
            json.dump(default_data["payments"], f, indent=2)
    
    # Initialize instructions.json
    if not INSTRUCTIONS_FILE.exists():
        with open(INSTRUCTIONS_FILE, 'w') as f:
            json.dump(default_data["instructions"], f, indent=2)

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load and save data functions
def load_data(file_path, default=[]):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return default

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

# Admin authentication
def authenticate(username, password):
    admin_data = load_data(ADMIN_FILE, {})
    if admin_data.get("username") == username:
        if admin_data.get("password") == hash_password(password):
            return True
    return False

def get_admin_data():
    return load_data(ADMIN_FILE, {})

def update_admin_data(data):
    save_data(ADMIN_FILE, data)

def get_payment_amount():
    admin_data = get_admin_data()
    return admin_data.get("payment_amount", 5000)

def get_payment_accounts():
    admin_data = get_admin_data()
    return admin_data.get("payment_accounts", [])

def get_short_url():
    admin_data = get_admin_data()
    base_url = admin_data.get("base_url", "http://localhost:8501")
    short_url_code = admin_data.get("short_url_code", "")
    return f"{base_url}/?student={short_url_code}"

def get_base_url():
    admin_data = get_admin_data()
    return admin_data.get("base_url", "http://localhost:8501")

def update_base_url(base_url):
    admin_data = get_admin_data()
    admin_data["base_url"] = base_url
    update_admin_data(admin_data)

def is_form_published():
    admin_data = get_admin_data()
    return admin_data.get("form_published", True)

def toggle_form_publish(status):
    admin_data = get_admin_data()
    admin_data["form_published"] = status
    update_admin_data(admin_data)

def get_contact_info():
    admin_data = get_admin_data()
    return {
        "email": admin_data.get("contact_email", "admin@example.com"),
        "phone": admin_data.get("contact_phone", "+91 9876543210")
    }

def update_contact_info(email, phone):
    admin_data = get_admin_data()
    admin_data["contact_email"] = email
    admin_data["contact_phone"] = phone
    update_admin_data(admin_data)

def get_tab_visibility():
    admin_data = get_admin_data()
    return admin_data.get("tab_visibility", {
        "account_details": True,
        "submit_payment": True,
        "payment_status": True,
        "student_list": True,
        "instructions": True
    })

def update_tab_visibility(tab_visibility):
    admin_data = get_admin_data()
    admin_data["tab_visibility"] = tab_visibility
    update_admin_data(admin_data)

def get_additional_instructions():
    admin_data = get_admin_data()
    return admin_data.get("additional_instructions", "")

def update_additional_instructions(instructions):
    admin_data = get_admin_data()
    admin_data["additional_instructions"] = instructions
    update_admin_data(admin_data)

# Student management
def get_students():
    return load_data(STUDENTS_FILE, [])

def save_students(students):
    save_data(STUDENTS_FILE, students)

def get_payments():
    return load_data(PAYMENT_FILE, [])

def save_payments(payments):
    save_data(PAYMENT_FILE, payments)

def get_student_by_id(student_id):
    students = get_students()
    for student in students:
        if student.get("id") == student_id:
            return student
    return None

def get_student_by_roll(roll_number):
    students = get_students()
    for student in students:
        if student.get("roll_number") == roll_number:
            return student
    return None

def get_student_payments(student_id):
    payments = get_payments()
    return [p for p in payments if p.get("student_id") == student_id]

def save_uploaded_file(uploaded_file, student_id):
    file_ext = uploaded_file.name.split('.')[-1]
    filename = f"{student_id}_{uuid.uuid4()}.{file_ext}"
    filepath = UPLOADS_DIR / filename
    
    with open(filepath, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    return filename

def get_instructions():
    return load_data(INSTRUCTIONS_FILE, "")

def save_instructions(instructions):
    save_data(INSTRUCTIONS_FILE, instructions)

# Main app
def main():
    init_files()
    
    # Check if student panel should be shown
    query_params = st.query_params
    if "student" in query_params:
        student_code = query_params["student"]
        admin_data = get_admin_data()
        if student_code == admin_data.get("short_url_code"):
            show_student_panel()
            return
        else:
            st.error("Invalid student portal URL")
            return
    
    # Show login/register page
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_admin_panel()

def show_login_page():
    st.title("🎓 Student Payment System - Admin Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if authenticate(username, password):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")

def show_student_panel():
    # Check if form is published
    if not is_form_published():
        show_unpublished_message()
        return
    
    # If form is published, show student panel with visible tabs
    st.title("🎓 Student Payment Portal")
    
    # Get admin data
    admin_data = get_admin_data()
    payment_amount = admin_data.get("payment_amount", 5000)
    payment_accounts = get_payment_accounts()
    tab_visibility = get_tab_visibility()
    
    # Create tabs based on visibility
    tab_names = []
    tab_functions = []
    
    if tab_visibility.get("account_details", True):
        tab_names.append("Account Details")
        tab_functions.append(lambda: show_account_details_section(payment_accounts, payment_amount, admin_data))
    
    if tab_visibility.get("submit_payment", True):
        tab_names.append("Submit Payment")
        tab_functions.append(lambda: show_submit_payment_section(payment_amount, payment_accounts))
    
    if tab_visibility.get("payment_status", True):
        tab_names.append("Payment Status")
        tab_functions.append(lambda: show_payment_status_section())
    
    if tab_visibility.get("student_list", True):
        tab_names.append("Student List")
        tab_functions.append(lambda: show_student_list_section())
    
    if tab_visibility.get("instructions", True):
        tab_names.append("Instructions")
        tab_functions.append(lambda: show_instructions_section())
    
    # Create tabs
    if tab_names:
        tabs = st.tabs(tab_names)
        for i, tab in enumerate(tabs):
            with tab:
                tab_functions[i]()
    else:
        st.warning("No tabs are currently available. Please contact administrator.")

def show_unpublished_message():
    """Show only a message when form is unpublished"""
    contact_info = get_contact_info()
    
    st.markdown(
        """
        <style>
        .unpublished-container {
            text-align: center;
            padding: 50px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            margin: 50px auto;
            max-width: 800px;
        }
        .unpublished-icon {
            font-size: 100px;
            margin-bottom: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        f"""
        <div class="unpublished-container">
            <div class="unpublished-icon">⏸️</div>
            <h1>Payment Form Currently Unavailable</h1>
            <h3>The payment submission form is temporarily unavailable.</h3>
            <p>Please check back later or contact the administrator for more information.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Display contact information without HTML formatting to prevent copy option
    st.markdown("---")
    st.markdown("### Contact Information")
    st.markdown("If you have urgent queries, please contact:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**📧 Email:** {contact_info['email']}")
    with col2:
        st.info(f"**📱 Phone:** {contact_info['phone']}")

def show_account_details_section(payment_accounts, payment_amount, admin_data):
    st.header("💰 Payment Account Details")
    
    if payment_accounts:
        st.success("Please make payment to one of the following accounts:")
        
        for i, account in enumerate(payment_accounts, 1):
            with st.container():
                st.markdown(f"### Account {i}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**Bank:** {account.get('bank', 'Not specified')}")
                with col2:
                    st.info(f"**Account Number:** {account.get('account', 'Not specified')}")
                with col3:
                    st.info(f"**Account Holder:** {account.get('name', 'Not specified')}")
                
                st.divider()
        
        # Payment amount
        st.warning(f"**IMPORTANT:** Payment amount is fixed at PKR{payment_amount}")
        
        # Additional instructions
        additional_instructions = get_additional_instructions()
        if additional_instructions:
            st.markdown("### Additional Instructions")
            st.info(additional_instructions)
    else:
        st.error("No payment account details available. Please contact administrator.")

def show_submit_payment_section(payment_amount, payment_accounts):
    st.header("Submit Payment Details")
    
    # Display payment amount reminder
    st.warning(f"Payment Amount: PKR{payment_amount} (fixed)")
    
    with st.form("student_payment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Student Name*")
            roll_number = st.text_input("Roll Number*")
        
        with col2:
            transaction_id = st.text_input("Transaction ID*")
            if payment_accounts:
                payment_account = st.selectbox(
                    "Select Payment Account*",
                    options=[f"{acc.get('bank')} - {acc.get('account')} - {acc.get('name')}" for acc in payment_accounts]
                )
            else:
                payment_account = "No accounts available"
                st.error("No payment accounts available. Please contact administrator.")
        
        payment_screenshot = st.file_uploader("Upload Payment Screenshot*", type=['png', 'jpg', 'jpeg'])
        remarks = st.text_area("Remarks (Optional)")
        
        # Required fields note
        st.caption("* Required fields")
        
        submitted = st.form_submit_button("Submit Payment")
        
        if submitted:
            if not all([name, roll_number, transaction_id, payment_screenshot]):
                st.error("Please fill all required fields")
            elif not payment_accounts:
                st.error("No payment accounts available. Please contact administrator.")
            else:
                # Check if roll number already exists
                students = get_students()
                existing = any(s.get("roll_number") == roll_number for s in students)
                
                if existing:
                    st.error("This roll number has already submitted payment")
                else:
                    # Create student record
                    student_id = str(uuid.uuid4())
                    student_data = {
                        "id": student_id,
                        "name": name,
                        "roll_number": roll_number,
                        "payment_status": "Pending",
                        "admin_remarks": "",
                        "registration_date": datetime.now().isoformat(),
                        "student_remarks": remarks,
                        "added_by_admin": False,
                        "payment_account_used": payment_account
                    }
                    
                    # Save payment record
                    filename = save_uploaded_file(payment_screenshot, student_id)
                    payment_data = {
                        "id": str(uuid.uuid4()),
                        "student_id": student_id,
                        "transaction_id": transaction_id,
                        "amount": payment_amount,
                        "screenshot": filename,
                        "status": "Pending",
                        "submission_date": datetime.now().isoformat(),
                        "student_remarks": remarks,
                        "payment_account": payment_account,
                        "added_by_admin": False
                    }
                    
                    # Save data
                    students.append(student_data)
                    save_students(students)
                    
                    payments = get_payments()
                    payments.append(payment_data)
                    save_payments(payments)
                    
                    st.success("Payment submitted successfully! Your payment is under review.")

def show_payment_status_section():
    st.header("Check Payment Status")
    
    roll_number = st.text_input("Enter your Roll Number to check status")
    if st.button("Check Status") and roll_number:
        student = get_student_by_roll(roll_number)
        
        if student:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Name", student.get("name"))
            with col2:
                st.metric("Roll Number", student.get("roll_number"))
            with col3:
                status = student.get("payment_status", "Pending")
                color = {"Paid": "green", "Unpaid": "red", "Pending": "orange"}.get(status, "gray")
                st.markdown(f"**Status:** <span style='color:{color};font-weight:bold'>{status}</span>", 
                          unsafe_allow_html=True)
            
            # Show payment account used
            if student.get("payment_account_used"):
                st.info(f"**Payment Account Used:** {student.get('payment_account_used')}")
            
            if student.get("admin_remarks"):
                st.info(f"**Admin Remarks:** {student.get('admin_remarks')}")
            
            # Show payment history
            payments = get_student_payments(student.get("id"))
            if payments:
                st.subheader("Payment History")
                for payment in payments:
                    with st.expander(f"Payment on {payment.get('submission_date')[:10]}"):
                        cols = st.columns(4)
                        cols[0].write(f"**Transaction ID:** {payment.get('transaction_id')}")
                        cols[1].write(f"**Amount:** PKR{payment.get('amount')}")
                        cols[2].write(f"**Status:** {payment.get('status')}")
                        cols[3].write(f"**Account:** {payment.get('payment_account', 'Not specified')}")
                        
                        if payment.get("student_remarks"):
                            st.write(f"**Your Remarks:** {payment.get('student_remarks')}")
        else:
            st.warning("No record found for this roll number")

def show_student_list_section():
    st.header("Student Payment List")
    
    students = get_students()
    if students:
        # Create DataFrames for paid and unpaid
        paid_students = [s for s in students if s.get("payment_status") == "Paid"]
        unpaid_students = [s for s in students if s.get("payment_status") in ["Unpaid", "Pending"]]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"✅ Paid Students ({len(paid_students)})")
            if paid_students:
                df_paid = pd.DataFrame([
                    {
                        "Name": s["name"], 
                        "Roll Number": s["roll_number"],
                        "Status": "Paid",
                        "Account Used": s.get("payment_account_used", "Not specified"),
                        "Registration Date": s.get("registration_date", "")[:10]
                    } 
                    for s in paid_students
                ])
                st.dataframe(df_paid, use_container_width=True)
            else:
                st.info("No paid students yet")
        
        with col2:
            st.subheader(f"❌ Unpaid/Pending ({len(unpaid_students)})")
            if unpaid_students:
                df_unpaid = pd.DataFrame([
                    {
                        "Name": s["name"], 
                        "Roll Number": s["roll_number"],
                        "Status": s.get("payment_status", "Pending"),
                        "Account Used": s.get("payment_account_used", "Not specified"),
                        "Registration Date": s.get("registration_date", "")[:10]
                    } 
                    for s in unpaid_students
                ])
                st.dataframe(df_unpaid, use_container_width=True)
            else:
                st.info("No unpaid students")
    else:
        st.info("No student records available")

def show_instructions_section():
    st.header("Instructions")
    instructions = get_instructions()
    if instructions:
        st.markdown(instructions)
    else:
        st.info("No instructions available from admin")

def show_admin_panel():
    st.sidebar.title("Admin Panel")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Student Management", "Payment Settings", "Reports", "Admin Settings"]
    )
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    
    if page == "Dashboard":
        show_admin_dashboard()
    elif page == "Student Management":
        show_student_management()
    elif page == "Payment Settings":
        show_payment_settings()
    elif page == "Reports":
        show_reports()
    elif page == "Admin Settings":
        show_admin_settings()

def show_admin_dashboard():
    st.title("📊 Admin Dashboard")
    
    # Statistics
    students = get_students()
    payments = get_payments()
    admin_data = get_admin_data()
    payment_accounts = get_payment_accounts()
    form_published = is_form_published()
    tab_visibility = get_tab_visibility()
    
    # Form status badge
    col_status, col1, col2, col3 = st.columns([1.5, 1, 1, 1])
    
    with col_status:
        status_color = "green" if form_published else "red"
        status_text = "🟢 PUBLISHED" if form_published else "🔴 UNPUBLISHED"
        st.markdown(f"<h3 style='color:{status_color};'>{status_text}</h3>", unsafe_allow_html=True)
        
        # Quick toggle button
        if form_published:
            if st.button("⏸️ Unpublish Form", type="secondary"):
                toggle_form_publish(False)
                st.success("Form has been unpublished! Students cannot access any tabs.")
                st.rerun()
        else:
            if st.button("▶️ Publish Form", type="primary"):
                toggle_form_publish(True)
                st.success("Form has been published! Students can now access enabled tabs.")
                st.rerun()
    
    with col1:
        st.metric("Total Students", len(students))
    with col2:
        paid_count = len([s for s in students if s.get("payment_status") == "Paid"])
        st.metric("Paid Students", paid_count)
    with col3:
        unpaid_count = len([s for s in students if s.get("payment_status") == "Unpaid"])
        st.metric("Unpaid Students", unpaid_count)
    
    # Form status message
    if not form_published:
        st.error("""
        ⚠️ **Student form is currently UNPUBLISHED.** 
        - Students cannot access any tabs
        - Students will only see an "unavailable" message
        - No student data or instructions will be visible
        """)
    else:
        st.success("""
        ✅ **Student form is PUBLISHED.** 
        - Students can access enabled tabs
        - Students can submit payments (if enabled)
        - Enabled student features are available
        """)
    
    # Short URL
    st.divider()
    st.subheader("Student Portal URL")
    
    short_url = get_short_url()
    base_url = get_base_url()
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.code(short_url)
    with col2:
        if st.button("📋 Copy URL", type="secondary", use_container_width=True):
            st.toast("URL copied to clipboard!", icon="✅")
    with col3:
        if st.button("🔗 Test URL", type="primary", use_container_width=True):
            st.toast(f"Testing URL: {short_url}", icon="🔗")
    
    st.info(f"**Base URL:** {base_url}")
    
    # Show what tabs are visible
    if form_published:
        visible_tabs = []
        if tab_visibility.get("account_details"): visible_tabs.append("1. Account Details")
        if tab_visibility.get("submit_payment"): visible_tabs.append("2. Submit Payment")
        if tab_visibility.get("payment_status"): visible_tabs.append("3. Payment Status")
        if tab_visibility.get("student_list"): visible_tabs.append("4. Student List")
        if tab_visibility.get("instructions"): visible_tabs.append("5. Instructions")
        
        if visible_tabs:
            st.success(f"Students can access: {', '.join(visible_tabs)}")
        else:
            st.warning("No tabs are enabled for students")
    else:
        st.warning("Students can only see: 'Payment Form Currently Unavailable' message")
    
    st.caption("Share this URL with students to access the payment portal")
    
    # Current payment accounts
    st.divider()
    st.subheader("Current Payment Accounts")
    if payment_accounts:
        for i, account in enumerate(payment_accounts, 1):
            cols = st.columns(3)
            cols[0].write(f"**Bank {i}:** {account.get('bank')}")
            cols[1].write(f"**Account:** {account.get('account')}")
            cols[2].write(f"**Holder:** {account.get('name')}")
    else:
        st.warning("No payment accounts set up")
    
    # Recent submissions
    st.divider()
    st.subheader("Recent Payment Submissions")
    
    if payments:
        recent_payments = sorted(payments, key=lambda x: x.get("submission_date", ""), reverse=True)[:10]
        
        for payment in recent_payments:
            student = get_student_by_id(payment.get("student_id"))
            if student:
                with st.expander(f"{student.get('name')} - {payment.get('submission_date')[:10]}"):
                    cols = st.columns(4)
                    cols[0].write(f"**Roll:** {student.get('roll_number')}")
                    cols[1].write(f"**Amount:** PKR{payment.get('amount')}")
                    cols[2].write(f"**Status:** {payment.get('status')}")
                    cols[3].write(f"**Txn ID:** {payment.get('transaction_id')}")
                    
                    if payment.get("payment_account"):
                        st.write(f"**Payment Account:** {payment.get('payment_account')}")
                    
                    # Show who submitted
                    submitted_by = "Admin" if payment.get("added_by_admin") else "Student"
                    st.write(f"**Submitted by:** {submitted_by}")
                    
                    # Quick actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Approve", key=f"approve_{payment['id']}"):
                            update_payment_status(student.get("id"), "Paid")
                            st.rerun()
                    with col2:
                        if st.button("Reject", key=f"reject_{payment['id']}"):
                            update_payment_status(student.get("id"), "Unpaid")
                            st.rerun()
                    with col3:
                        # View screenshot button (if exists)
                        if payment.get("screenshot"):
                            screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                            if screenshot_path.exists():
                                with open(screenshot_path, "rb") as f:
                                    img_bytes = f.read()
                                st.download_button(
                                    "Download Screenshot",
                                    img_bytes,
                                    file_name=payment.get("screenshot"),
                                    key=f"download_{payment['id']}"
                            )
    else:
        st.info("No payment submissions yet")

def update_payment_status(student_id, status):
    students = get_students()
    for student in students:
        if student.get("id") == student_id:
            student["payment_status"] = status
            break
    save_students(students)
    
    payments = get_payments()
    for payment in payments:
        if payment.get("student_id") == student_id:
            payment["status"] = status
            break
    save_payments(payments)

def show_student_management():
    st.title("👥 Student Management")
    
    tab1, tab2 = st.tabs(["Manage Students", "Add New Student"])
    
    with tab1:
        students = get_students()
        
        if students:
            # Filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_status = st.selectbox("Filter by Status", ["All", "Paid", "Unpaid", "Pending"])
            with col2:
                search_term = st.text_input("Search by Name or Roll Number")
            with col3:
                filter_added_by = st.selectbox("Added By", ["All", "Admin", "Student"])
            
            # Apply filters
            filtered_students = students
            if filter_status != "All":
                filtered_students = [s for s in filtered_students if s.get("payment_status") == filter_status]
            if search_term:
                filtered_students = [s for s in filtered_students 
                                   if search_term.lower() in s.get("name", "").lower() 
                                   or search_term in s.get("roll_number", "")]
            if filter_added_by != "All":
                if filter_added_by == "Admin":
                    filtered_students = [s for s in filtered_students if s.get("added_by_admin") == True]
                else:
                    filtered_students = [s for s in filtered_students if s.get("added_by_admin") != True]
            
            # Display students in a table
            if filtered_students:
                # Create DataFrame for better display
                df = pd.DataFrame([
                    {
                        "Name": s.get("name", ""),
                        "Roll Number": s.get("roll_number", ""),
                        "Payment Status": s.get("payment_status", "Pending"),
                        "Account Used": s.get("payment_account_used", "Not specified"),
                        "Admin Remarks": s.get("admin_remarks", ""),
                        "Added By": "Admin" if s.get("added_by_admin") else "Student",
                        "Registration Date": s.get("registration_date", "")[:10] if s.get("registration_date") else ""
                    }
                    for s in filtered_students
                ])
                
                # Display the dataframe
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Individual student management below the table
                st.subheader("Manage Individual Students")
                for student in filtered_students:
                    with st.expander(f"Manage: {student.get('name')} (Roll: {student.get('roll_number')})"):
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                        
                        with col1:
                            st.write(f"**Name:** {student.get('name')}")
                        with col2:
                            st.write(f"**Roll Number:** {student.get('roll_number')}")
                        with col3:
                            added_by = "Admin" if student.get("added_by_admin") else "Student"
                            st.write(f"**Added By:** {added_by}")
                        with col4:
                            status = student.get("payment_status", "Pending")
                            color = {"Paid": "green", "Unpaid": "red", "Pending": "orange"}.get(status, "gray")
                            st.markdown(f"**Status:** <span style='color:{color}'>{status}</span>", 
                                      unsafe_allow_html=True)
                        
                        # Show payment account used
                        if student.get("payment_account_used"):
                            st.info(f"**Payment Account Used:** {student.get('payment_account_used')}")
                        
                        # Status update section
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            # Status update dropdown
                            new_status = st.selectbox(
                                "Update Status",
                                ["Paid", "Unpaid", "Pending"],
                                index=["Paid", "Unpaid", "Pending"].index(status),
                                key=f"status_{student['id']}"
                            )
                        with col2:
                            st.write("")  # Spacer
                            if new_status != status:
                                if st.button("Update Status", key=f"update_{student['id']}"):
                                    update_payment_status(student.get("id"), new_status)
                                    st.success("Status updated!")
                                    st.rerun()
                        
                        # Update payment account used
                        payment_accounts = get_payment_accounts()
                        if payment_accounts:
                            current_account = student.get("payment_account_used", "")
                            account_options = [f"{acc.get('bank')} - {acc.get('account')} - {acc.get('name')}" for acc in payment_accounts]
                            
                            if current_account not in account_options and current_account:
                                account_options.insert(0, current_account)
                            
                            new_account = st.selectbox(
                                "Update Payment Account Used",
                                options=account_options,
                                index=account_options.index(current_account) if current_account in account_options else 0,
                                key=f"account_{student['id']}"
                            )
                            
                            if new_account != current_account:
                                if st.button("Update Account", key=f"update_acc_{student['id']}"):
                                    student["payment_account_used"] = new_account
                                    save_students(students)
                                    
                                    # Update payment record if exists
                                    payments = get_payments()
                                    for payment in payments:
                                        if payment.get("student_id") == student.get("id"):
                                            payment["payment_account"] = new_account
                                            break
                                    save_payments(payments)
                                    
                                    st.success("Payment account updated!")
                                    st.rerun()
                        
                        # Admin remarks
                        admin_remarks = st.text_area(
                            "Admin Remarks",
                            value=student.get("admin_remarks", ""),
                            key=f"remarks_{student['id']}",
                            height=100
                        )
                        if admin_remarks != student.get("admin_remarks", ""):
                            if st.button("Save Remarks", key=f"save_remarks_{student['id']}"):
                                student["admin_remarks"] = admin_remarks
                                save_students(students)
                                st.success("Remarks updated!")
                                st.rerun()
                        
                        # Delete student button
                        if st.button("Delete Student", key=f"delete_{student['id']}", type="secondary"):
                            # Remove student from students list
                            updated_students = [s for s in students if s.get("id") != student.get("id")]
                            save_students(updated_students)
                            
                            # Remove student's payments
                            payments = get_payments()
                            updated_payments = [p for p in payments if p.get("student_id") != student.get("id")]
                            save_payments(updated_payments)
                            
                            # Delete uploaded files if any
                            student_payments = get_student_payments(student.get("id"))
                            for payment in student_payments:
                                if payment.get("screenshot"):
                                    screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                                    if screenshot_path.exists():
                                        screenshot_path.unlink()
                            
                            st.success("Student deleted successfully!")
                            st.rerun()
            else:
                st.info("No students found matching your criteria")
        else:
            st.info("No students found")
    
    with tab2:
        st.subheader("Add New Student Manually")
        
        # Load payment accounts for dropdown
        payment_accounts = get_payment_accounts()
        payment_amount = get_payment_amount()
        
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Student Name*", help="Full name of the student")
                roll_number = st.text_input("Roll Number*", help="Unique roll number")
                payment_status = st.selectbox(
                    "Payment Status*", 
                    ["Paid", "Unpaid", "Pending"],
                    help="Select current payment status"
                )
                
                # Payment account selection (required for Paid status)
                if payment_accounts:
                    account_options = [f"{acc.get('bank')} - {acc.get('account')} - {acc.get('name')}" for acc in payment_accounts]
                    account_options.insert(0, "Select Account")
                    
                    if payment_status == "Paid":
                        selected_account = st.selectbox(
                            "Payment Account Used*",
                            options=account_options,
                            index=1 if len(account_options) > 1 else 0,
                            help="Select which account the student paid to"
                        )
                    else:
                        selected_account = st.selectbox(
                            "Payment Account Used",
                            options=account_options,
                            index=0,
                            help="Select if known, or leave as 'Select Account'"
                        )
                else:
                    st.warning("No payment accounts configured. Please add accounts in Payment Settings.")
                    selected_account = None
                
            with col2:
                transaction_id = st.text_input(
                    "Transaction ID", 
                    help="Enter transaction ID if payment is made"
                )
                amount_paid = st.number_input(
                    "Amount Paid (PK)*",
                    min_value=0,
                    value=payment_amount if payment_status == "Paid" else 0,
                    help="Enter the amount student actually paid"
                )
                admin_remarks = st.text_area("Admin Remarks", help="Any remarks from admin")
                payment_date = st.date_input(
                    "Payment Date",
                    value=datetime.now().date(),
                    help="Date when payment was made"
                )
            
            submitted = st.form_submit_button("Add Student")
            
            if submitted:
                if not name or not roll_number:
                    st.error("Please fill all required fields (Name and Roll Number)")
                elif payment_status == "Paid" and (not selected_account or selected_account == "Select Account"):
                    st.error("Please select a payment account for paid student")
                elif payment_status == "Paid" and amount_paid <= 0:
                    st.error("Please enter a valid amount for paid student")
                elif payment_status == "Paid" and not transaction_id:
                    st.warning("Transaction ID is recommended for paid students")
                    # Allow without transaction ID but ask for confirmation
                    if st.button("Confirm Add Without Transaction ID"):
                        add_student_with_details(
                            name, roll_number, payment_status, selected_account, 
                            transaction_id, amount_paid, admin_remarks, payment_date
                        )
                else:
                    add_student_with_details(
                        name, roll_number, payment_status, selected_account, 
                        transaction_id, amount_paid, admin_remarks, payment_date
                    )

def add_student_with_details(name, roll_number, payment_status, selected_account, 
                            transaction_id, amount_paid, admin_remarks, payment_date):
    """Helper function to add student with all details"""
    students = get_students()
    
    # Check for duplicate roll number
    if any(s.get("roll_number") == roll_number for s in students):
        st.error("Roll number already exists")
        return
    
    student_id = str(uuid.uuid4())
    student_data = {
        "id": student_id,
        "name": name,
        "roll_number": roll_number,
        "payment_status": payment_status,
        "admin_remarks": admin_remarks,
        "registration_date": datetime.now().isoformat(),
        "student_remarks": "",
        "added_by_admin": True,
        "payment_account_used": selected_account if selected_account != "Select Account" else None
    }
    
    students.append(student_data)
    save_students(students)
    
    # If student is marked as paid, also create a payment record
    if payment_status == "Paid" and amount_paid > 0:
        payment_data = {
            "id": str(uuid.uuid4()),
            "student_id": student_id,
            "transaction_id": transaction_id or f"ADMIN-ADDED-{roll_number}",
            "amount": amount_paid,
            "screenshot": None,
            "status": "Paid",
            "submission_date": payment_date.isoformat(),
            "student_remarks": "",
            "admin_remarks": admin_remarks,
            "payment_account": selected_account if selected_account != "Select Account" else "Not specified",
            "added_by_admin": True,
            "verified_by_admin": True
        }
        
        payments = get_payments()
        payments.append(payment_data)
        save_payments(payments)
    
    st.success("Student added successfully!")
    st.balloons()
    st.rerun()

def show_payment_settings():
    st.title("💰 Payment Settings")
    
    admin_data = get_admin_data()
    form_published = is_form_published()
    contact_info = get_contact_info()
    tab_visibility = get_tab_visibility()
    base_url = get_base_url()
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Basic Settings", "Account Details", "Form Control", "Tab Visibility", "Contact Info", "Instructions"])
    
    with tab1:
        st.subheader("Payment Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            payment_amount = st.number_input(
                "Payment Amount (PKR)",
                min_value=0,
                value=admin_data.get("payment_amount", 5000)
            )
            
        with col2:
            # Base URL Configuration
            new_base_url = st.text_input(
                "Base URL",
                value=base_url,
                help="Change this when deploying to a different server (e.g., https://your-domain.com)"
            )
        
        # Generate new short URL code
        if st.button("Generate New Student URL Code"):
            admin_data["short_url_code"] = str(uuid.uuid4())[:8]
            update_admin_data(admin_data)
            st.success("New URL code generated!")
            st.rerun()
        
        # Current URL with copy button
        st.subheader("Student Portal URL")
        short_url = get_short_url()
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.code(short_url)
        with col2:
            if st.button("📋 Copy", type="secondary", use_container_width=True):
                st.toast("URL copied to clipboard!", icon="✅")
        with col3:
            if st.button("🔗 Test", type="primary", use_container_width=True):
                st.toast(f"Testing URL: {short_url}", icon="🔗")
        
        # URL format info
        st.info(f"**URL Format:** {base_url}/?student=[code]")
        
        if st.button("Save All Settings"):
            # Update payment amount
            admin_data["payment_amount"] = payment_amount
            
            # Update base URL if changed
            if new_base_url != base_url:
                admin_data["base_url"] = new_base_url.strip()
                st.success(f"Base URL updated to: {new_base_url}")
            
            update_admin_data(admin_data)
            st.success("Settings saved successfully!")
    
    with tab2:
        st.subheader("Payment Account Details")
        st.info("These account details will be displayed to students in the payment portal")
        
        accounts = admin_data.get("payment_accounts", [])
        
        for i, account in enumerate(accounts):
            st.divider()
            st.write(f"**Account {i+1}**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                bank = st.text_input("Bank Name", value=account.get("bank", ""), key=f"bank_{i}")
            with col2:
                account_no = st.text_input("Account Number", value=account.get("account", ""), key=f"account_{i}")
            with col3:
                account_name = st.text_input("Account Holder Name", value=account.get("name", ""), key=f"name_{i}")
            
            accounts[i] = {"bank": bank, "account": account_no, "name": account_name}
        
        # Add new account button
        if st.button("Add Another Account"):
            accounts.append({"bank": "", "account": "", "name": ""})
            admin_data["payment_accounts"] = accounts
            update_admin_data(admin_data)
            st.rerun()
        
        # Remove account button
        if len(accounts) > 1 and st.button("Remove Last Account"):
            accounts.pop()
            admin_data["payment_accounts"] = accounts
            update_admin_data(admin_data)
            st.rerun()
        
        # Save accounts
        if st.button("Save Account Details"):
            admin_data["payment_accounts"] = accounts
            update_admin_data(admin_data)
            st.success("Account details saved!")
    
    with tab3:
        st.subheader("📋 Form Control Center")
        
        # Current status
        status_color = "green" if form_published else "red"
        status_icon = "✅" if form_published else "❌"
        status_text = "PUBLISHED" if form_published else "UNPUBLISHED"
        
        st.markdown(f"""
        <div style='background-color:{status_color}20; padding:20px; border-radius:10px; border-left:5px solid {status_color};'>
            <h3>{status_icon} Form Status: <span style='color:{status_color}'>{status_text}</span></h3>
            <p>When the form is unpublished, students see only an "unavailable" message.</p>
            <p>No tabs, no student list, no instructions - nothing is accessible.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Publish Form")
            st.info("Make the payment form available to students")
            if st.button("▶️ Publish Form Now", type="primary", use_container_width=True):
                toggle_form_publish(True)
                st.success("✅ Form has been published! Students can now access enabled tabs.")
                st.rerun()
        
        with col2:
            st.subheader("Unpublish Form")
            st.warning("Completely hide the student portal")
            if st.button("⏸️ Unpublish Form Now", type="secondary", use_container_width=True):
                toggle_form_publish(False)
                st.warning("⏸️ Form has been unpublished! Students will see only an 'unavailable' message.")
                st.rerun()
        
        st.divider()
        
        # Additional Instructions
        st.subheader("Additional Instructions")
        st.info("These instructions appear in the Account Details tab for students")
        
        additional_instructions = st.text_area(
            "Enter additional instructions for students",
            value=get_additional_instructions(),
            height=200
        )
        
        if st.button("Save Additional Instructions"):
            update_additional_instructions(additional_instructions)
            st.success("Additional instructions saved!")
        
        # Form statistics
        st.divider()
        st.subheader("Form Statistics")
        
        students = get_students()
        payments = get_payments()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Submissions", len(payments))
        with col2:
            pending_count = len([p for p in payments if p.get("status") == "Pending"])
            st.metric("Pending Review", pending_count)
        with col3:
            today = datetime.now().date().isoformat()
            today_count = len([p for p in payments if p.get("submission_date", "").startswith(today)])
            st.metric("Today's Submissions", today_count)
    
    with tab4:
        st.subheader("📊 Tab Visibility Control")
        st.info("Control which tabs are visible to students in the payment portal")
        
        # Get current visibility
        tab_visibility = get_tab_visibility()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Enable/Disable Tabs")
            
            account_details = st.checkbox(
                "Account Details Tab",
                value=tab_visibility.get("account_details", True),
                help="Shows payment account details and instructions"
            )
            
            submit_payment = st.checkbox(
                "Submit Payment Tab",
                value=tab_visibility.get("submit_payment", True),
                help="Allows students to submit payment forms"
            )
            
            payment_status = st.checkbox(
                "Payment Status Tab",
                value=tab_visibility.get("payment_status", True),
                help="Allows students to check their payment status"
            )
        
        with col2:
            st.write("### ")  # Empty header for alignment
            
            student_list = st.checkbox(
                "Student List Tab",
                value=tab_visibility.get("student_list", True),
                help="Shows list of paid and unpaid students"
            )
            
            instructions = st.checkbox(
                "Instructions Tab",
                value=tab_visibility.get("instructions", True),
                help="Shows general instructions from admin"
            )
        
        # Save button
        if st.button("Save Tab Visibility Settings"):
            new_visibility = {
                "account_details": account_details,
                "submit_payment": submit_payment,
                "payment_status": payment_status,
                "student_list": student_list,
                "instructions": instructions
            }
            update_tab_visibility(new_visibility)
            st.success("Tab visibility settings saved!")
        
        # Preview what students see
        st.divider()
        st.subheader("Student View Preview")
        
        if form_published:
            visible_tabs = []
            if account_details: visible_tabs.append("1. Account Details - Payment accounts info")
            if submit_payment: visible_tabs.append("2. Submit Payment - Payment submission form")
            if payment_status: visible_tabs.append("3. Payment Status - Check payment status")
            if student_list: visible_tabs.append("4. Student List - View paid/unpaid students")
            if instructions: visible_tabs.append("5. Instructions - Admin instructions")
            
            if visible_tabs:
                st.success("**Students see:** Access to enabled tabs with complete functionality")
                st.code("\n".join(visible_tabs))
            else:
                st.error("**Students see:** No tabs available (all tabs are disabled)")
        else:
            st.error("**Students see:** Only an 'unavailable' message with contact info")
            
            # Show preview of what students will see
            st.markdown("**Preview of unpublished form:**")
            st.markdown(
                f"""
                <div style='border: 2px dashed #666; padding: 20px; border-radius: 10px; background: #f9f9f9;'>
                    <div style='text-align: center;'>
                        <h2>⏸️ Payment Form Currently Unavailable</h2>
                        <p>The payment submission form is temporarily unavailable.</p>
                        <p>Please check back later or contact the administrator for more information.</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Contact info preview without HTML formatting
            st.markdown("**Contact Information Preview:**")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📧 Email: {contact_info['email']}")
            with col2:
                st.info(f"📱 Phone: {contact_info['phone']}")
    
    with tab5:
        st.subheader("📞 Contact Information")
        st.info("This contact information will be shown to students when the form is unpublished")
        
        current_email = contact_info['email']
        current_phone = contact_info['phone']
        
        with st.form("contact_info_form"):
            email = st.text_input("Contact Email", value=current_email)
            phone = st.text_input("Contact Phone Number", value=current_phone)
            
            submitted = st.form_submit_button("Save Contact Information")
            
            if submitted:
                update_contact_info(email, phone)
                st.success("Contact information saved successfully!")
    
    with tab6:
        st.subheader("Instructions for Students")
        st.info("These instructions appear in the Instructions tab for students")
        
        instructions = st.text_area(
            "Enter instructions that will appear in the student panel",
            value=get_instructions(),
            height=300
        )
        
        if st.button("Save Instructions"):
            save_instructions(instructions)
            st.success("Instructions saved!")

def show_reports():
    st.title("📈 Reports & Exports")
    
    students = get_students()
    payments = get_payments()
    
    tab1, tab2, tab3 = st.tabs(["Student Data", "Payment Data", "Analytics"])
    
    with tab1:
        st.subheader("Export Student Data")
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox("Select Format", ["CSV", "Excel"])
        with col2:
            filter_status = st.selectbox("Filter by Payment Status", ["All", "Paid", "Unpaid", "Pending"])
        
        if students:
            # Filter students
            filtered_students = students
            if filter_status != "All":
                filtered_students = [s for s in students if s.get("payment_status") == filter_status]
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    "Name": s.get("name"),
                    "Roll Number": s.get("roll_number"),
                    "Payment Status": s.get("payment_status"),
                    "Payment Account Used": s.get("payment_account_used", ""),
                    "Admin Remarks": s.get("admin_remarks", ""),
                    "Student Remarks": s.get("student_remarks", ""),
                    "Added By": "Admin" if s.get("added_by_admin") else "Student",
                    "Registration Date": s.get("registration_date", "")[:10] if s.get("registration_date") else ""
                }
                for s in filtered_students
            ])
            
            if not df.empty:
                if export_format == "CSV":
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        file_name=f"students_{filter_status.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Students')
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        "Download Excel",
                        excel_data,
                        file_name=f"students_{filter_status.lower()}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            else:
                st.info("No data to export for selected filter")
        else:
            st.info("No student data to export")
    
    with tab2:
        st.subheader("Export Payment Data")
        
        col1, col2 = st.columns(2)
        with col1:
            payment_export_format = st.selectbox("Export Format", ["CSV", "Excel"], key="payment_format")
        with col2:
            payment_filter = st.selectbox("Filter Payments by Status", ["All", "Paid", "Unpaid", "Pending"], key="payment_filter")
        
        if payments:
            # Filter payments
            filtered_payments = payments
            if payment_filter != "All":
                filtered_payments = [p for p in payments if p.get("status") == payment_filter]
            
            # Get student info for each payment
            payment_data = []
            for payment in filtered_payments:
                student = get_student_by_id(payment.get("student_id"))
                if student:
                    payment_data.append({
                        "Student Name": student.get("name"),
                        "Roll Number": student.get("roll_number"),
                        "Transaction ID": payment.get("transaction_id"),
                        "Amount": payment.get("amount"),
                        "Status": payment.get("status"),
                        "Payment Account": payment.get("payment_account", ""),
                        "Submitted By": "Admin" if payment.get("added_by_admin") else "Student",
                        "Submission Date": payment.get("submission_date", "")[:10],
                        "Admin Remarks": payment.get("admin_remarks", ""),
                        "Student Remarks": payment.get("student_remarks", "")
                    })
            
            if payment_data:
                df_payments = pd.DataFrame(payment_data)
                
                if payment_export_format == "CSV":
                    csv = df_payments.to_csv(index=False)
                    st.download_button(
                        "Download Payment CSV",
                        csv,
                        file_name=f"payments_{payment_filter.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_payments.to_excel(writer, index=False, sheet_name='Payments')
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        "Download Payment Excel",
                        excel_data,
                        file_name=f"payments_{payment_filter.lower()}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            else:
                st.info("No payment data to export")
        
        st.divider()
        st.subheader("Download Payment Screenshots")
        
        screenshot_filter = st.selectbox("Filter by Status", ["All", "Paid", "Unpaid", "Pending"], key="screenshot_filter")
        
        if st.button("Download Screenshots as ZIP", use_container_width=True):
            # Get filtered payments
            filtered_payments = payments
            if screenshot_filter != "All":
                filtered_payments = [p for p in payments if p.get("status") == screenshot_filter]
            
            # Filter payments with screenshots
            payments_with_screenshots = [p for p in filtered_payments if p.get("screenshot")]
            
            if not payments_with_screenshots:
                st.warning("No screenshots found for the selected filter")
            else:
                # Create ZIP file in memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for payment in payments_with_screenshots:
                        file_path = UPLOADS_DIR / payment.get("screenshot")
                        if file_path.exists():
                            # Get student info for better file naming
                            student = get_student_by_id(payment.get("student_id"))
                            if student:
                                new_name = f"{student.get('roll_number')}_{student.get('name')}_{payment.get('screenshot')}"
                                zip_file.write(file_path, new_name)
                
                zip_data = zip_buffer.getvalue()
                
                st.download_button(
                    "Download ZIP",
                    zip_data,
                    file_name=f"payment_screenshots_{screenshot_filter.lower()}_{datetime.now().strftime('%Y%m%d')}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
    
    with tab3:
        st.subheader("Analytics & Insights")
        
        if students and payments:
            # Status distribution
            status_counts = {}
            for student in students:
                status = student.get("payment_status", "Pending")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Payment Status Distribution**")
                status_df = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
                st.bar_chart(status_df.set_index('Status'))
            
            with col2:
                st.write("**Submission Source**")
                admin_added = len([s for s in students if s.get("added_by_admin")])
                student_submitted = len(students) - admin_added
                
                source_data = pd.DataFrame({
                    'Source': ['Admin Added', 'Student Submitted'],
                    'Count': [admin_added, student_submitted]
                })
                st.bar_chart(source_data.set_index('Source'))
            
            # Payment summary
            st.divider()
            st.subheader("Payment Summary")
            
            total_amount = sum(p.get("amount", 0) for p in payments if p.get("status") == "Paid")
            total_paid_count = len([p for p in payments if p.get("status") == "Paid"])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Amount Collected", f"PKR{total_amount:,}")
            with col2:
                st.metric("Total Paid Transactions", total_paid_count)
            with col3:
                avg_amount = total_amount / total_paid_count if total_paid_count > 0 else 0
                st.metric("Average Payment", f"PKR{avg_amount:,.2f}")
            
            # Payment by account analysis
            st.divider()
            st.subheader("Payment Account Analysis")
            
            account_summary = {}
            for payment in payments:
                if payment.get("status") == "Paid":
                    account = payment.get("payment_account", "Not specified")
                    account_summary[account] = account_summary.get(account, 0) + payment.get("amount", 0)
            
            if account_summary:
                account_df = pd.DataFrame(list(account_summary.items()), columns=['Account', 'Amount'])
                st.dataframe(account_df.sort_values('Amount', ascending=False), use_container_width=True)
            
            # Recent activity
            st.divider()
            st.subheader("Recent Activity")
            
            recent_payments = sorted(payments, key=lambda x: x.get("submission_date", ""), reverse=True)[:5]
            
            for payment in recent_payments:
                student = get_student_by_id(payment.get("student_id"))
                if student:
                    col1, col2, col3 = st.columns([3, 2, 2])
                    with col1:
                        st.write(f"**{student.get('name')}** ({student.get('roll_number')})")
                    with col2:
                        st.write(f"PKR{payment.get('amount')} - {payment.get('status')}")
                    with col3:
                        st.write(f"{payment.get('submission_date', '')[:10]}")
                    st.divider()

def show_admin_settings():
    st.title("⚙️ Admin Settings")
    
    admin_data = get_admin_data()
    
    tab1, tab2 = st.tabs(["Change Credentials", "System Info"])
    
    with tab1:
        st.subheader("Change Username and Password")
        
        with st.form("change_credentials"):
            current_password = st.text_input("Current Password", type="password")
            new_username = st.text_input("New Username", value=admin_data.get("username", ""))
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submitted = st.form_submit_button("Update Credentials")
            
            if submitted:
                if not authenticate(admin_data.get("username"), current_password):
                    st.error("Current password is incorrect")
                elif new_password != confirm_password:
                    st.error("New passwords don't match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    admin_data["username"] = new_username
                    admin_data["password"] = hash_password(new_password)
                    update_admin_data(admin_data)
                    st.success("Credentials updated successfully!")
    
    with tab2:
        st.subheader("System Information")
        
        students = get_students()
        payments = get_payments()
        contact_info = get_contact_info()
        tab_visibility = get_tab_visibility()
        base_url = get_base_url()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"Total Students: {len(students)}")
            st.info(f"Total Payments: {len(payments)}")
            st.info(f"Payment Amount: PKR{admin_data.get('payment_amount', 5000)}")
            st.info(f"Form Status: {'Published' if is_form_published() else 'Unpublished'}")
            st.info(f"Base URL: {base_url}")
            st.info(f"Student URL Code: {admin_data.get('short_url_code')}")
        
        with col2:
            st.info(f"Upload Directory: {UPLOADS_DIR}")
            st.info(f"Data Directory: {DATA_DIR}")
            st.info(f"Payment Accounts: {len(get_payment_accounts())}")
            st.info(f"Contact Email: {contact_info['email']}")
            st.info(f"Contact Phone: {contact_info['phone']}")
            st.info(f"Admin Added Students: {len([s for s in students if s.get('added_by_admin')])}")
        
        # Tab visibility status
        st.divider()
        st.subheader("Tab Visibility Status")
        
        visible_tabs = []
        if tab_visibility.get("account_details"): visible_tabs.append("Account Details")
        if tab_visibility.get("submit_payment"): visible_tabs.append("Submit Payment")
        if tab_visibility.get("payment_status"): visible_tabs.append("Payment Status")
        if tab_visibility.get("student_list"): visible_tabs.append("Student List")
        if tab_visibility.get("instructions"): visible_tabs.append("Instructions")
        
        st.success(f"Visible tabs for students: {', '.join(visible_tabs) if visible_tabs else 'None'}")
        
        # Full student URL
        st.divider()
        st.subheader("Full Student Portal URL")
        st.code(get_short_url())
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy Full URL", use_container_width=True):
                st.toast("Full URL copied to clipboard!", icon="✅")
        with col2:
            if st.button("🔗 Test Full URL", use_container_width=True):
                st.toast(f"Testing: {get_short_url()}", icon="🔗")
        
        # Data backup
        st.divider()
        st.subheader("Data Backup")
        
        if st.button("Export All Data as Backup", use_container_width=True):
            all_data = {
                "students": get_students(),
                "admin": get_admin_data(),
                "payments": get_payments(),
                "instructions": get_instructions()
            }
            
            json_data = json.dumps(all_data, indent=2)
            st.download_button(
                "Download Backup",
                json_data,
                file_name=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
import streamlit as st
import json
import os
import uuid
import base64
import zipfile
import io
import pandas as pd
from datetime import datetime, timedelta
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
            "base_url": "https://payment-collection-form.streamlit.app",
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
            },
            "screenshot_settings": {
                "allow_download": True,
                "allow_delete": True,
                "max_file_size_mb": 5
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

# Query params handling for different Streamlit versions
def get_query_params():
    """Handle query parameters for both old and new Streamlit versions"""
    try:
        # Try Streamlit >= 1.28.0 method
        if hasattr(st, 'query_params'):
            params = st.query_params.to_dict()
            return params
    except:
        pass
    
    try:
        # Try Streamlit < 1.28.0 method
        if hasattr(st, 'experimental_get_query_params'):
            params = st.experimental_get_query_params()
            # Convert to dict format
            result = {}
            for key, value in params.items():
                if isinstance(value, list) and len(value) == 1:
                    result[key] = value[0]
                else:
                    result[key] = value
            return result
    except:
        pass
    
    # Return empty dict if both methods fail
    return {}

# Format date and time display
def format_datetime(dt_string):
    """Format datetime string to readable format"""
    try:
        if not dt_string:
            return "Not specified"
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%d-%m-%Y %I:%M %p")
    except:
        return dt_string

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

def get_screenshot_settings():
    admin_data = get_admin_data()
    return admin_data.get("screenshot_settings", {
        "allow_download": True,
        "allow_delete": True,
        "max_file_size_mb": 5
    })

def update_screenshot_settings(settings):
    admin_data = get_admin_data()
    admin_data["screenshot_settings"] = settings
    update_admin_data(admin_data)

def get_short_url():
    admin_data = get_admin_data()
    base_url = admin_data.get("base_url", "https://payment-collection-form.streamlit.app")
    short_url_code = admin_data.get("short_url_code", "")
    # Ensure no trailing slash
    base_url = base_url.rstrip('/')
    return f"{base_url}/?student={short_url_code}"

def get_base_url():
    admin_data = get_admin_data()
    base_url = admin_data.get("base_url", "https://payment-collection-form.streamlit.app")
    # Remove trailing slash for consistency
    return base_url.rstrip('/')

def update_base_url(base_url):
    admin_data = get_admin_data()
    # Remove trailing slash before saving
    admin_data["base_url"] = base_url.rstrip('/')
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

# Student deletion function
def delete_student_by_id(student_id):
    """Delete a student and all associated data"""
    students = get_students()
    payments = get_payments()
    
    # Find student
    student_to_delete = None
    for student in students:
        if student.get("id") == student_id:
            student_to_delete = student
            break
    
    if not student_to_delete:
        return False
    
    # Delete student's screenshot files
    student_payments = [p for p in payments if p.get("student_id") == student_id]
    for payment in student_payments:
        if payment.get("screenshot"):
            delete_screenshot_file(payment.get("screenshot"))
    
    # Remove student from students list
    updated_students = [s for s in students if s.get("id") != student_id]
    save_students(updated_students)
    
    # Remove student's payments
    updated_payments = [p for p in payments if p.get("student_id") != student_id]
    save_payments(updated_payments)
    
    return True

def delete_multiple_students(student_ids):
    """Delete multiple students and their associated data"""
    success_count = 0
    fail_count = 0
    
    for student_id in student_ids:
        if delete_student_by_id(student_id):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count

# Screenshot management
def delete_screenshot_file(filename):
    """Delete screenshot file from server"""
    try:
        if filename:
            file_path = UPLOADS_DIR / filename
            if file_path.exists():
                file_path.unlink()
                return True
    except Exception as e:
        st.error(f"Error deleting screenshot: {e}")
    return False

def remove_screenshot_from_payment(payment_id):
    """Remove screenshot reference from payment record"""
    payments = get_payments()
    for payment in payments:
        if payment.get("id") == payment_id:
            payment["screenshot"] = None
            payment["screenshot_deleted"] = True
            payment["screenshot_deleted_date"] = datetime.now().isoformat()
            break
    save_payments(payments)

def remove_screenshot_from_student(student_id):
    """Remove screenshot reference from student record"""
    students = get_students()
    for student in students:
        if student.get("id") == student_id:
            student["screenshot_deleted"] = True
            break
    save_students(students)

def view_screenshot(filename):
    """View screenshot in modal"""
    if filename:
        file_path = UPLOADS_DIR / filename
        if file_path.exists():
            with open(file_path, "rb") as f:
                img_bytes = f.read()
            return img_bytes
    return None

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
    screenshot_settings = get_screenshot_settings()
    max_size_mb = screenshot_settings.get("max_file_size_mb", 5)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if uploaded_file.size > max_size_bytes:
        raise ValueError(f"File size exceeds maximum allowed size of {max_size_mb}MB")
    
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
    query_params = get_query_params()
    
    # DEBUG: Show query params (set to False in production)
    DEBUG_MODE = False
    if DEBUG_MODE:
        st.sidebar.write("🔍 DEBUG INFO")
        st.sidebar.write("Query Params:", query_params)
        admin_data = get_admin_data()
        st.sidebar.write("Admin Code:", admin_data.get("short_url_code"))
        st.sidebar.write("Base URL:", get_base_url())
        st.sidebar.write("Full URL:", get_short_url())
    
    if "student" in query_params:
        student_code = query_params["student"]
        admin_data = get_admin_data()
        
        if DEBUG_MODE:
            st.sidebar.write("Student Code from URL:", student_code)
            st.sidebar.write("Code Match:", student_code == admin_data.get("short_url_code"))
        
        if student_code == admin_data.get("short_url_code"):
            show_student_panel()
            return
        else:
            st.error("❌ Invalid student portal URL")
            # Show login option even if URL is invalid
            pass
    
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
        
        # Student portal link
        st.markdown("---")
        st.markdown("### Student Portal")
        admin_data = get_admin_data()
        short_url = get_short_url()
        st.info(f"Student Portal URL: `{short_url}`")
        if st.button("📋 Copy Student URL"):
            st.toast("Student URL copied to clipboard!", icon="✅")

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
    screenshot_settings = get_screenshot_settings()
    
    # Create tabs based on visibility
    tab_names = []
    tab_functions = []
    
    if tab_visibility.get("account_details", True):
        tab_names.append("Account Details")
        tab_functions.append(lambda: show_account_details_section(payment_accounts, payment_amount, admin_data))
    
    if tab_visibility.get("submit_payment", True):
        tab_names.append("Submit Payment")
        tab_functions.append(lambda: show_submit_payment_section(payment_amount, payment_accounts, screenshot_settings))
    
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
        st.warning(f"**IMPORTANT:** Payment amount is fixed at PKR {payment_amount}")
        
        # Additional instructions
        additional_instructions = get_additional_instructions()
        if additional_instructions:
            st.markdown("### Additional Instructions")
            st.info(additional_instructions)
    else:
        st.error("No payment account details available. Please contact administrator.")

def show_submit_payment_section(payment_amount, payment_accounts, screenshot_settings):
    st.header("Submit Payment Details")
    
    # Display payment amount reminder
    st.warning(f"Payment Amount: PKR {payment_amount} (fixed)")
    
    max_file_size = screenshot_settings.get("max_file_size_mb", 5)
    
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
        
        payment_screenshot = st.file_uploader(
            f"Upload Payment Screenshot* (Max: {max_file_size}MB)",
            type=['png', 'jpg', 'jpeg'],
            help=f"Maximum file size: {max_file_size}MB"
        )
        remarks = st.text_area("Remarks (Optional)")
        
        # Show current timestamp info
        current_time = datetime.now()
        formatted_time = current_time.strftime("%d-%m-%Y %I:%M %p")
        st.info(f"**Payment Timestamp will be automatically recorded as:** {formatted_time}")
        
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
                    try:
                        # Auto-set payment datetime to current time
                        payment_datetime = datetime.now()
                        
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
                            "payment_account_used": payment_account,
                            "payment_datetime": payment_datetime.isoformat(),  # Auto-set timestamp
                            "auto_timestamp": True,  # Flag to indicate auto-generated timestamp
                            "screenshot_deleted": False
                        }
                        
                        # Save payment record
                        filename = save_uploaded_file(payment_screenshot, student_id)
                        payment_data = {
                            "id": str(uuid.uuid4()),
                            "student_id": student_id,
                            "transaction_id": transaction_id,
                            "amount": payment_amount,
                            "screenshot": filename,
                            "screenshot_deleted": False,
                            "status": "Pending",
                            "submission_date": datetime.now().isoformat(),
                            "payment_datetime": payment_datetime.isoformat(),  # Auto-set timestamp
                            "student_remarks": remarks,
                            "payment_account": payment_account,
                            "added_by_admin": False,
                            "auto_timestamp": True  # Flag to indicate auto-generated timestamp
                        }
                        
                        # Save data
                        students.append(student_data)
                        save_students(students)
                        
                        payments = get_payments()
                        payments.append(payment_data)
                        save_payments(payments)
                        
                        st.success("Payment submitted successfully! Your payment is under review.")
                        st.info(f"Submission timestamp: {formatted_time}")
                        
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

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
            
            # Show payment date and time
            if student.get("payment_datetime"):
                formatted_datetime = format_datetime(student.get("payment_datetime"))
                # Check if timestamp was auto-generated
                if student.get("auto_timestamp"):
                    st.info(f"**Payment Submission Timestamp:** {formatted_datetime} (Auto-recorded)")
                else:
                    st.info(f"**Payment Date & Time:** {formatted_datetime}")
            
            # Check if screenshot was deleted
            if student.get("screenshot_deleted"):
                st.warning("⚠️ Payment screenshot has been deleted by admin")
            
            if student.get("admin_remarks"):
                st.info(f"**Admin Remarks:** {student.get('admin_remarks')}")
            
            # Show payment history
            payments = get_student_payments(student.get("id"))
            if payments:
                st.subheader("Payment History")
                for payment in payments:
                    payment_date = format_datetime(payment.get("payment_datetime", payment.get("submission_date")))
                    with st.expander(f"Payment on {payment_date}"):
                        cols = st.columns(4)
                        cols[0].write(f"**Transaction ID:** {payment.get('transaction_id')}")
                        cols[1].write(f"**Amount:** PKR {payment.get('amount')}")
                        cols[2].write(f"**Status:** {payment.get('status')}")
                        cols[3].write(f"**Account:** {payment.get('payment_account', 'Not specified')}")
                        
                        # Show payment date and time
                        if payment.get("payment_datetime"):
                            formatted_datetime = format_datetime(payment.get("payment_datetime"))
                            if payment.get("auto_timestamp"):
                                st.write(f"**Submission Timestamp:** {formatted_datetime} (Auto-recorded)")
                            else:
                                st.write(f"**Payment Date & Time:** {formatted_datetime}")
                        
                        # Show submission date
                        submission_date = format_datetime(payment.get("submission_date"))
                        st.write(f"**Form Submission Date:** {submission_date}")
                        
                        # Check if screenshot exists or was deleted
                        if payment.get("screenshot_deleted"):
                            st.warning("📸 Screenshot has been deleted")
                        elif payment.get("screenshot"):
                            screenshot_settings = get_screenshot_settings()
                            if screenshot_settings.get("allow_download", True):
                                screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                                if screenshot_path.exists():
                                    with open(screenshot_path, "rb") as f:
                                        img_bytes = f.read()
                                    st.download_button(
                                        "📥 Download Screenshot",
                                        img_bytes,
                                        file_name=payment.get("screenshot"),
                                        key=f"student_download_{payment['id']}",
                                        help="Download the payment screenshot"
                                    )
                                else:
                                    st.warning("⚠️ Screenshot file not found on server")
                            else:
                                st.info("📸 Screenshot is available (download disabled by admin)")
                        else:
                            st.info("📸 No screenshot uploaded")
                        
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
                        "Payment Date": format_datetime(s.get("payment_datetime", "")),
                        "Registration Date": format_datetime(s.get("registration_date", ""))
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
                        "Payment Date": format_datetime(s.get("payment_datetime", "")),
                        "Registration Date": format_datetime(s.get("registration_date", ""))
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
        ["Dashboard", "Student Management", "Payment Settings", "Reports", "Admin Settings", "Screenshot Management"]
    )
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    
    # Student portal quick link
    st.sidebar.markdown("---")
    st.sidebar.subheader("Student Portal")
    short_url = get_short_url()
    st.sidebar.code(short_url[:40] + "..." if len(short_url) > 40 else short_url)
    if st.sidebar.button("📋 Copy Student URL", use_container_width=True):
        st.toast("Student URL copied to clipboard!", icon="✅")
    
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
    elif page == "Screenshot Management":
        show_screenshot_management()

def show_admin_dashboard():
    st.title("📊 Admin Dashboard")
    
    # Statistics
    students = get_students()
    payments = get_payments()
    admin_data = get_admin_data()
    payment_accounts = get_payment_accounts()
    form_published = is_form_published()
    tab_visibility = get_tab_visibility()
    screenshot_settings = get_screenshot_settings()
    
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
        if st.button("🔗 Open in New Tab", type="primary", use_container_width=True):
            st.markdown(f'<a href="{short_url}" target="_blank">Click here to open</a>', unsafe_allow_html=True)
    
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
    
    # Screenshot settings info
    st.divider()
    st.subheader("Screenshot Settings")
    allow_download = screenshot_settings.get("allow_download", True)
    allow_delete = screenshot_settings.get("allow_delete", True)
    max_size = screenshot_settings.get("max_file_size_mb", 5)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status = "✅ Enabled" if allow_download else "❌ Disabled"
        st.info(f"**Download:** {status}")
    with col2:
        status = "✅ Enabled" if allow_delete else "❌ Disabled"
        st.info(f"**Delete:** {status}")
    with col3:
        st.info(f"**Max Size:** {max_size}MB")
    
    # Recent submissions
    st.divider()
    st.subheader("Recent Payment Submissions")
    
    if payments:
        # Sort by payment datetime if available, otherwise by submission date
        recent_payments = sorted(
            payments, 
            key=lambda x: x.get("payment_datetime", x.get("submission_date", "")), 
            reverse=True
        )[:10]
        
        for payment in recent_payments:
            student = get_student_by_id(payment.get("student_id"))
            if student:
                payment_date = format_datetime(payment.get("payment_datetime", payment.get("submission_date")))
                with st.expander(f"{student.get('name')} - {payment_date}"):
                    cols = st.columns(4)
                    cols[0].write(f"**Roll:** {student.get('roll_number')}")
                    cols[1].write(f"**Amount:** PKR {payment.get('amount')}")
                    cols[2].write(f"**Status:** {payment.get('status')}")
                    cols[3].write(f"**Txn ID:** {payment.get('transaction_id')}")
                    
                    # Show payment date and time
                    if payment.get("payment_datetime"):
                        formatted_datetime = format_datetime(payment.get("payment_datetime"))
                        if payment.get("auto_timestamp"):
                            st.write(f"**Submission Timestamp:** {formatted_datetime} (Auto-recorded)")
                        else:
                            st.write(f"**Payment Date & Time:** {formatted_datetime}")
                    
                    # Show submission date
                    submission_date = format_datetime(payment.get("submission_date"))
                    st.write(f"**Form Submission Date:** {submission_date}")
                    
                    if payment.get("payment_account"):
                        st.write(f"**Payment Account:** {payment.get('payment_account')}")
                    
                    # Show who submitted
                    submitted_by = "Admin" if payment.get("added_by_admin") else "Student"
                    st.write(f"**Submitted by:** {submitted_by}")
                    
                    # Show timestamp type
                    if payment.get("auto_timestamp"):
                        st.write("**Timestamp Type:** Auto-generated (Student submission)")
                    else:
                        st.write("**Timestamp Type:** Manually set by Admin")
                    
                    # Screenshot management section
                    st.divider()
                    st.subheader("Screenshot Management")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # View screenshot button
                        if payment.get("screenshot") and not payment.get("screenshot_deleted"):
                            screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                            if screenshot_path.exists():
                                with open(screenshot_path, "rb") as f:
                                    img_bytes = f.read()
                                
                                # Display image in a modal or directly
                                if st.button("👁️ View", key=f"view_{payment['id']}", use_container_width=True):
                                    st.image(img_bytes, caption="Payment Screenshot", use_column_width=True)
                            else:
                                st.warning("File not found")
                        elif payment.get("screenshot_deleted"):
                            st.warning("❌ Deleted")
                        else:
                            st.info("No screenshot")
                    
                    with col2:
                        # Download screenshot button
                        if payment.get("screenshot") and not payment.get("screenshot_deleted"):
                            screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                            if screenshot_path.exists():
                                with open(screenshot_path, "rb") as f:
                                    img_bytes = f.read()
                                
                                if screenshot_settings.get("allow_download", True):
                                    st.download_button(
                                        "📥 Download",
                                        img_bytes,
                                        file_name=payment.get("screenshot"),
                                        key=f"download_{payment['id']}",
                                        use_container_width=True
                                    )
                                else:
                                    st.warning("Download disabled")
                            else:
                                st.warning("File not found")
                        elif payment.get("screenshot_deleted"):
                            st.warning("❌ Deleted")
                        else:
                            st.info("No screenshot")
                    
                    with col3:
                        # Delete screenshot button
                        if payment.get("screenshot") and not payment.get("screenshot_deleted"):
                            if screenshot_settings.get("allow_delete", True):
                                if st.button("🗑️ Delete", key=f"delete_{payment['id']}", type="secondary", use_container_width=True):
                                    if delete_screenshot_file(payment.get("screenshot")):
                                        remove_screenshot_from_payment(payment.get("id"))
                                        remove_screenshot_from_student(payment.get("student_id"))
                                        st.success("Screenshot deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete screenshot")
                            else:
                                st.warning("Delete disabled")
                        elif payment.get("screenshot_deleted"):
                            st.info("Already deleted")
                        else:
                            st.info("No screenshot")
                    
                    with col4:
                        # Quick actions for payment status
                        col_status1, col_status2 = st.columns(2)
                        with col_status1:
                            if payment.get("status") != "Paid":
                                if st.button("✅ Approve", key=f"approve_{payment['id']}", use_container_width=True):
                                    update_payment_status(student.get("id"), "Paid")
                                    st.rerun()
                        with col_status2:
                            if payment.get("status") != "Unpaid":
                                if st.button("❌ Reject", key=f"reject_{payment['id']}", use_container_width=True):
                                    update_payment_status(student.get("id"), "Unpaid")
                                    st.rerun()
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
    
    tab1, tab2, tab3 = st.tabs(["Manage Students", "Add New Student", "Bulk Delete Students"])
    
    with tab1:
        students = get_students()
        
        if students:
            # Filter options
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                filter_status = st.selectbox("Filter by Status", ["All", "Paid", "Unpaid", "Pending"])
            with col2:
                search_term = st.text_input("Search by Name or Roll Number")
            with col3:
                filter_added_by = st.selectbox("Added By", ["All", "Admin", "Student"])
            with col4:
                date_filter = st.selectbox("Filter by Date", ["All", "Today", "Last 7 Days", "This Month"])
            
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
            
            # Date filter
            if date_filter != "All":
                today = datetime.now().date()
                filtered_by_date = []
                for student in filtered_students:
                    payment_datetime = student.get("payment_datetime")
                    if payment_datetime:
                        try:
                            payment_date = datetime.fromisoformat(payment_datetime).date()
                            if date_filter == "Today" and payment_date == today:
                                filtered_by_date.append(student)
                            elif date_filter == "Last 7 Days" and (today - payment_date).days <= 7:
                                filtered_by_date.append(student)
                            elif date_filter == "This Month" and payment_date.month == today.month and payment_date.year == today.year:
                                filtered_by_date.append(student)
                        except:
                            pass
                filtered_students = filtered_by_date
            
            # Display students in a table
            if filtered_students:
                # Create DataFrame for better display
                df = pd.DataFrame([
                    {
                        "Name": s.get("name", ""),
                        "Roll Number": s.get("roll_number", ""),
                        "Payment Status": s.get("payment_status", "Pending"),
                        "Payment Date": format_datetime(s.get("payment_datetime", "")),
                        "Timestamp Type": "Auto" if s.get("auto_timestamp") else "Manual",
                        "Account Used": s.get("payment_account_used", "Not specified"),
                        "Admin Remarks": s.get("admin_remarks", ""),
                        "Added By": "Admin" if s.get("added_by_admin") else "Student",
                        "Registration Date": format_datetime(s.get("registration_date", ""))
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
                        
                        # Show payment date and time
                        if student.get("payment_datetime"):
                            formatted_datetime = format_datetime(student.get("payment_datetime"))
                            timestamp_type = "Auto-generated (Student submission)" if student.get("auto_timestamp") else "Manually set by Admin"
                            st.info(f"**Payment Date & Time:** {formatted_datetime}")
                            st.info(f"**Timestamp Type:** {timestamp_type}")
                        
                        # Show payment account used
                        if student.get("payment_account_used"):
                            st.info(f"**Payment Account Used:** {student.get('payment_account_used')}")
                        
                        # Check if screenshot was deleted
                        if student.get("screenshot_deleted"):
                            st.warning("⚠️ Payment screenshot has been deleted")
                        
                        # Show payment history with screenshot management
                        st.subheader("Payment History & Screenshot Management")
                        payments = get_student_payments(student.get("id"))
                        if payments:
                            for payment in payments:
                                with st.expander(f"Payment: {payment.get('transaction_id')} - {payment.get('status')}"):
                                    col_info1, col_info2 = st.columns(2)
                                    with col_info1:
                                        st.write(f"**Amount:** PKR {payment.get('amount')}")
                                        st.write(f"**Date:** {format_datetime(payment.get('payment_datetime'))}")
                                    with col_info2:
                                        st.write(f"**Account:** {payment.get('payment_account')}")
                                        st.write(f"**Status:** {payment.get('status')}")
                                    
                                    # Screenshot section
                                    st.write("**Screenshot:**")
                                    screenshot_settings = get_screenshot_settings()
                                    
                                    if payment.get("screenshot_deleted"):
                                        st.warning("🗑️ Screenshot has been deleted")
                                    elif payment.get("screenshot"):
                                        col_ss1, col_ss2, col_ss3 = st.columns(3)
                                        
                                        with col_ss1:
                                            # View button
                                            screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                                            if screenshot_path.exists():
                                                with open(screenshot_path, "rb") as f:
                                                    img_bytes = f.read()
                                                if st.button("👁️ View", key=f"view_payment_{payment['id']}", use_container_width=True):
                                                    st.image(img_bytes, caption="Payment Screenshot", use_column_width=True)
                                            else:
                                                st.warning("File not found")
                                        
                                        with col_ss2:
                                            # Download button
                                            if screenshot_path.exists():
                                                with open(screenshot_path, "rb") as f:
                                                    img_bytes = f.read()
                                                if screenshot_settings.get("allow_download", True):
                                                    st.download_button(
                                                        "📥 Download",
                                                        img_bytes,
                                                        file_name=payment.get("screenshot"),
                                                        key=f"download_payment_{payment['id']}",
                                                        use_container_width=True
                                                    )
                                                else:
                                                    st.warning("Download disabled")
                                            else:
                                                st.warning("File not found")
                                        
                                        with col_ss3:
                                            # Delete button
                                            if screenshot_settings.get("allow_delete", True):
                                                if st.button("🗑️ Delete", key=f"delete_payment_{payment['id']}", type="secondary", use_container_width=True):
                                                    if delete_screenshot_file(payment.get("screenshot")):
                                                        remove_screenshot_from_payment(payment.get("id"))
                                                        remove_screenshot_from_student(payment.get("student_id"))
                                                        st.success("Screenshot deleted successfully!")
                                                        st.rerun()
                                                    else:
                                                        st.error("Failed to delete screenshot")
                                            else:
                                                st.warning("Delete disabled")
                                    else:
                                        st.info("No screenshot uploaded")
                                    
                                    # Quick status update
                                    col_status1, col_status2 = st.columns(2)
                                    with col_status1:
                                        if payment.get("status") != "Paid":
                                            if st.button("✅ Mark as Paid", key=f"paid_{payment['id']}", use_container_width=True):
                                                payment["status"] = "Paid"
                                                save_payments(payments)
                                                student["payment_status"] = "Paid"
                                                save_students(students)
                                                st.success("Payment marked as Paid!")
                                                st.rerun()
                                    with col_status2:
                                        if payment.get("status") != "Unpaid":
                                            if st.button("❌ Mark as Unpaid", key=f"unpaid_{payment['id']}", use_container_width=True):
                                                payment["status"] = "Unpaid"
                                                save_payments(payments)
                                                student["payment_status"] = "Unpaid"
                                                save_students(students)
                                                st.success("Payment marked as Unpaid!")
                                                st.rerun()
                        
                        # Update payment date and time (Admin can modify)
                        st.subheader("Update Payment Date & Time")
                        st.warning("Admin can modify the payment timestamp if needed")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if student.get("payment_datetime"):
                                current_dt = datetime.fromisoformat(student.get("payment_datetime"))
                            else:
                                current_dt = datetime.now()
                            
                            new_payment_date = st.date_input(
                                "New Payment Date",
                                value=current_dt.date(),
                                key=f"date_{student['id']}"
                            )
                        with col2:
                            new_payment_time = st.time_input(
                                "New Payment Time",
                                value=current_dt.time(),
                                key=f"time_{student['id']}"
                            )
                        
                        new_payment_datetime = datetime.combine(new_payment_date, new_payment_time)
                        
                        if new_payment_datetime.isoformat() != student.get("payment_datetime"):
                            if st.button("Update Payment Date/Time", key=f"update_dt_{student['id']}"):
                                student["payment_datetime"] = new_payment_datetime.isoformat()
                                student["auto_timestamp"] = False  # Mark as manually set by admin
                                
                                # Update payment record if exists
                                payments = get_payments()
                                for payment in payments:
                                    if payment.get("student_id") == student.get("id"):
                                        payment["payment_datetime"] = new_payment_datetime.isoformat()
                                        payment["auto_timestamp"] = False  # Mark as manually set by admin
                                        break
                                save_payments(payments)
                                
                                save_students(students)
                                st.success("Payment date/time updated!")
                                st.rerun()
                        
                        # Status update section
                        st.subheader("Update Payment Status")
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
                                    delete_screenshot_file(payment.get("screenshot"))
                            
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
                
                # Payment date and time (optional for admin)
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    payment_date = st.date_input(
                        "Payment Date (Optional)",
                        value=datetime.now().date(),
                        help="Leave as today's date for auto-timestamp"
                    )
                with col_date2:
                    payment_time = st.time_input(
                        "Payment Time (Optional)",
                        value=datetime.now().time(),
                        help="Leave as current time for auto-timestamp"
                    )
                
                # Combine date and time
                payment_datetime = datetime.combine(payment_date, payment_time)
                
                st.info("Note: Payment timestamp will be recorded automatically if not specified")
                
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
                    "Amount Paid (PKR)*",
                    min_value=0,
                    value=payment_amount if payment_status == "Paid" else 0,
                    help="Enter the amount student actually paid"
                )
                admin_remarks = st.text_area("Admin Remarks", help="Any remarks from admin", height=100)
                
                # Additional information
                submitted_by = st.selectbox(
                    "Submitted By",
                    ["Student", "Admin"],
                    help="Who submitted this payment information"
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
                            transaction_id, amount_paid, admin_remarks, 
                            payment_datetime, submitted_by
                        )
                else:
                    add_student_with_details(
                        name, roll_number, payment_status, selected_account, 
                        transaction_id, amount_paid, admin_remarks, 
                        payment_datetime, submitted_by
                    )

    with tab3:
        st.subheader("🗑️ Bulk Delete Students")
        st.warning("⚠️ **WARNING:** This action cannot be undone! All selected students and their data will be permanently deleted.")
        
        students = get_students()
        
        if students:
            # Filter options for bulk delete
            col1, col2 = st.columns(2)
            with col1:
                bulk_filter_status = st.selectbox("Filter by Status", ["All", "Paid", "Unpaid", "Pending"], key="bulk_filter")
            with col2:
                bulk_search = st.text_input("Search by Name or Roll Number", key="bulk_search")
            
            # Apply filters
            filtered_students = students
            if bulk_filter_status != "All":
                filtered_students = [s for s in filtered_students if s.get("payment_status") == bulk_filter_status]
            
            if bulk_search:
                filtered_students = [s for s in filtered_students 
                                   if bulk_search.lower() in s.get("name", "").lower() 
                                   or bulk_search in s.get("roll_number", "")]
            
            if filtered_students:
                # Create a DataFrame for display with checkboxes
                st.info(f"Found {len(filtered_students)} students matching your criteria")
                
                # Create checkboxes for each student
                selected_students = []
                
                # Display in groups of 10 for better performance
                for i in range(0, len(filtered_students), 10):
                    group = filtered_students[i:i+10]
                    
                    for student in group:
                        col1, col2, col3, col4 = st.columns([1, 3, 3, 2])
                        with col1:
                            selected = st.checkbox("", key=f"select_{student['id']}")
                            if selected:
                                selected_students.append(student["id"])
                        with col2:
                            st.write(f"**{student.get('name')}**")
                        with col3:
                            st.write(f"Roll: {student.get('roll_number')}")
                        with col4:
                            status = student.get("payment_status", "Pending")
                            color = {"Paid": "green", "Unpaid": "red", "Pending": "orange"}.get(status, "gray")
                            st.markdown(f"<span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
                    
                    st.divider()
                
                # Summary of selected students
                if selected_students:
                    st.subheader(f"Selected {len(selected_students)} Students for Deletion")
                    
                    # Show details of selected students
                    selected_student_details = []
                    for student_id in selected_students:
                        student = get_student_by_id(student_id)
                        if student:
                            selected_student_details.append({
                                "Name": student.get("name"),
                                "Roll Number": student.get("roll_number"),
                                "Status": student.get("payment_status"),
                                "Payment Date": format_datetime(student.get("payment_datetime", ""))
                            })
                    
                    if selected_student_details:
                        df_selected = pd.DataFrame(selected_student_details)
                        st.dataframe(df_selected, use_container_width=True)
                    
                    # Confirmation for deletion
                    st.error("""
                    **Deletion will permanently remove:**
                    - Student records
                    - All payment records
                    - Uploaded screenshots
                    - All associated data
                    """)
                    
                    # Double confirmation
                    confirm_text = st.text_input("Type 'DELETE' to confirm")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Delete Selected Students", type="secondary", disabled=confirm_text != "DELETE"):
                            if confirm_text == "DELETE":
                                with st.spinner("Deleting selected students..."):
                                    success_count, fail_count = delete_multiple_students(selected_students)
                                    
                                    if success_count > 0:
                                        st.success(f"Successfully deleted {success_count} students!")
                                        if fail_count > 0:
                                            st.warning(f"Failed to delete {fail_count} students")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete any students")
                            else:
                                st.warning("Please type 'DELETE' to confirm")
                    
                    with col2:
                        if st.button("Clear Selection"):
                            st.rerun()
                else:
                    st.info("Select students by checking the boxes to enable deletion")
            else:
                st.info("No students found matching your criteria")
        else:
            st.info("No students found to delete")

def add_student_with_details(name, roll_number, payment_status, selected_account, 
                            transaction_id, amount_paid, admin_remarks, 
                            payment_datetime, submitted_by):
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
        "added_by_admin": submitted_by == "Admin",
        "payment_account_used": selected_account if selected_account != "Select Account" else None,
        "payment_datetime": payment_datetime.isoformat(),
        "auto_timestamp": submitted_by == "Student",  # Auto-timestamp only for student submissions
        "screenshot_deleted": False
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
            "screenshot_deleted": False,
            "status": "Paid",
            "submission_date": datetime.now().isoformat(),
            "payment_datetime": payment_datetime.isoformat(),
            "student_remarks": "",
            "admin_remarks": admin_remarks,
            "payment_account": selected_account if selected_account != "Select Account" else "Not specified",
            "added_by_admin": submitted_by == "Admin",
            "auto_timestamp": submitted_by == "Student",
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
        
        # Payment Amount and Base URL in a form
        with st.form("basic_settings_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                payment_amount = st.number_input(
                    "Payment Amount (PKR)*",
                    min_value=0,
                    value=admin_data.get("payment_amount", 5000),
                    help="Set the fixed payment amount for students"
                )
                
            with col2:
                # Base URL Configuration
                new_base_url = st.text_input(
                    "Base URL*",
                    value=base_url,
                    help="Your app URL (e.g., https://payment-collection-form.streamlit.app)"
                )
            
            # Generate new short URL code option
            generate_new_code = st.checkbox("Generate new student URL code", value=False)
            
            # Save button
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                save_button = st.form_submit_button("💾 Save Basic Settings", use_container_width=True)
            
            if save_button:
                if not payment_amount or not new_base_url:
                    st.error("Please fill all required fields (*)")
                else:
                    # Update payment amount
                    admin_data["payment_amount"] = payment_amount
                    
                    # Update base URL if changed
                    if new_base_url != base_url:
                        admin_data["base_url"] = new_base_url.strip().rstrip('/')
                        st.success(f"Base URL updated to: {new_base_url}")
                    
                    # Generate new short URL code if requested
                    if generate_new_code:
                        admin_data["short_url_code"] = str(uuid.uuid4())[:8]
                        st.success("New student URL code generated!")
                    
                    update_admin_data(admin_data)
                    st.success("Basic settings saved successfully!")
                    st.rerun()
        
        # Important note about Streamlit Cloud
        st.warning("""
        **Important for Streamlit Cloud:**
        1. Your Base URL should be: `https://payment-collection-form.streamlit.app`
        2. Make sure there's no trailing slash at the end
        3. Student portal URL format: `https://payment-collection-form.streamlit.app/?student=YOUR_CODE`
        """)
        
        # Test URL button
        if st.button("Test Student Portal URL"):
            test_url = f"{base_url}/?student={admin_data.get('short_url_code')}"
            st.info(f"**Test URL:** {test_url}")
            st.markdown(f'<a href="{test_url}" target="_blank">Open Test URL in New Tab</a>', unsafe_allow_html=True)
        
        # Current URL display
        st.divider()
        st.subheader("Current Student Portal URL")
        
        short_url = get_short_url()
        st.code(short_url)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy URL", use_container_width=True):
                st.toast("URL copied to clipboard!", icon="✅")
        with col2:
            st.markdown(f'<a href="{short_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%;">🔗 Open Portal</button></a>', unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Payment Account Details")
        st.info("These account details will be displayed to students in the payment portal")
        
        accounts = admin_data.get("payment_accounts", [])
        
        # Display current accounts in a form
        with st.form("account_details_form"):
            st.write("**Current Accounts:**")
            
            account_changes = []
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
                
                account_changes.append({"bank": bank, "account": account_no, "name": account_name})
            
            # Save button
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("💾 Save Account Details", use_container_width=True):
                    admin_data["payment_accounts"] = account_changes
                    update_admin_data(admin_data)
                    st.success("Account details saved!")
                    st.rerun()
        
        # Add/Remove account buttons (outside form to avoid rerun issues)
        st.divider()
        st.write("**Quick Actions:**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add New Account"):
                accounts.append({"bank": "", "account": "", "name": ""})
                admin_data["payment_accounts"] = accounts
                update_admin_data(admin_data)
                st.success("New account added!")
                st.rerun()
        
        with col2:
            if len(accounts) > 1:
                if st.button("➖ Remove Last Account"):
                    accounts.pop()
                    admin_data["payment_accounts"] = accounts
                    update_admin_data(admin_data)
                    st.success("Last account removed!")
                    st.rerun()
            else:
                st.button("➖ Remove Last Account", disabled=True, help="Cannot remove the only account")
    
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
        
        # Additional Instructions with save button
        st.subheader("Additional Instructions")
        st.info("These instructions appear in the Account Details tab for students")
        
        with st.form("additional_instructions_form"):
            additional_instructions = st.text_area(
                "Enter additional instructions for students",
                value=get_additional_instructions(),
                height=200
            )
            
            if st.form_submit_button("💾 Save Additional Instructions"):
                update_additional_instructions(additional_instructions)
                st.success("Additional instructions saved!")
                st.rerun()
        
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
        
        # Tab visibility settings in a form
        with st.form("tab_visibility_form"):
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
            if st.form_submit_button("💾 Save Tab Visibility Settings"):
                new_visibility = {
                    "account_details": account_details,
                    "submit_payment": submit_payment,
                    "payment_status": payment_status,
                    "student_list": student_list,
                    "instructions": instructions
                }
                update_tab_visibility(new_visibility)
                st.success("Tab visibility settings saved!")
                st.rerun()
        
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
            email = st.text_input("Contact Email*", value=current_email)
            phone = st.text_input("Contact Phone Number*", value=current_phone)
            
            if st.form_submit_button("💾 Save Contact Information"):
                if email and phone:
                    update_contact_info(email, phone)
                    st.success("Contact information saved successfully!")
                    st.rerun()
                else:
                    st.error("Please fill all required fields (*)")
    
    with tab6:
        st.subheader("Instructions for Students")
        st.info("These instructions appear in the Instructions tab for students")
        
        with st.form("instructions_form"):
            instructions = st.text_area(
                "Enter instructions that will appear in the student panel",
                value=get_instructions(),
                height=300
            )
            
            if st.form_submit_button("💾 Save Instructions"):
                save_instructions(instructions)
                st.success("Instructions saved!")
                st.rerun()

def show_screenshot_management():
    st.title("📸 Screenshot Management")
    
    screenshot_settings = get_screenshot_settings()
    
    tab1, tab2, tab3 = st.tabs(["Settings", "Bulk Operations", "Statistics"])
    
    with tab1:
        st.subheader("Screenshot Settings")
        
        with st.form("screenshot_settings_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                allow_download = st.checkbox(
                    "Allow Screenshot Download",
                    value=screenshot_settings.get("allow_download", True),
                    help="Enable/disable download option for screenshots"
                )
                
                allow_delete = st.checkbox(
                    "Allow Screenshot Deletion",
                    value=screenshot_settings.get("allow_delete", True),
                    help="Enable/disable delete option for screenshots"
                )
            
            with col2:
                max_file_size = st.number_input(
                    "Maximum File Size (MB)*",
                    min_value=1,
                    max_value=50,
                    value=screenshot_settings.get("max_file_size_mb", 5),
                    help="Maximum allowed file size for uploaded screenshots"
                )
            
            if st.form_submit_button("💾 Save Settings"):
                new_settings = {
                    "allow_download": allow_download,
                    "allow_delete": allow_delete,
                    "max_file_size_mb": max_file_size
                }
                update_screenshot_settings(new_settings)
                st.success("Screenshot settings saved!")
                st.rerun()
        
        # Current statistics
        st.divider()
        st.subheader("Current Statistics")
        
        payments = get_payments()
        total_screenshots = len([p for p in payments if p.get("screenshot")])
        deleted_screenshots = len([p for p in payments if p.get("screenshot_deleted")])
        active_screenshots = total_screenshots - deleted_screenshots
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Screenshots", total_screenshots)
        with col2:
            st.metric("Active Screenshots", active_screenshots)
        with col3:
            st.metric("Deleted Screenshots", deleted_screenshots)
    
    with tab2:
        st.subheader("Bulk Screenshot Operations")
        st.warning("⚠️ These operations affect multiple records at once. Use with caution!")
        
        payments = get_payments()
        
        if payments:
            # Filter options for bulk operations
            col1, col2 = st.columns(2)
            with col1:
                bulk_filter_status = st.selectbox("Filter by Status", ["All", "Paid", "Unpaid", "Pending"])
            with col2:
                bulk_filter_date = st.selectbox("Filter by Date", ["All", "Today", "Last 7 Days", "This Month"])
            
            # Apply filters
            filtered_payments = payments
            if bulk_filter_status != "All":
                filtered_payments = [p for p in filtered_payments if p.get("status") == bulk_filter_status]
            
            if bulk_filter_date != "All":
                today = datetime.now().date()
                filtered_by_date = []
                for payment in filtered_payments:
                    payment_datetime = payment.get("payment_datetime")
                    if payment_datetime:
                        try:
                            payment_date = datetime.fromisoformat(payment_datetime).date()
                            if bulk_filter_date == "Today" and payment_date == today:
                                filtered_by_date.append(payment)
                            elif bulk_filter_date == "Last 7 Days" and (today - payment_date).days <= 7:
                                filtered_by_date.append(payment)
                            elif bulk_filter_date == "This Month" and payment_date.month == today.month and payment_date.year == today.year:
                                filtered_by_date.append(payment)
                        except:
                            pass
                filtered_payments = filtered_by_date
            
            # Count screenshots in filtered results
            screenshots_to_process = [p for p in filtered_payments if p.get("screenshot") and not p.get("screenshot_deleted")]
            
            st.info(f"Found {len(screenshots_to_process)} screenshots matching your criteria")
            
            if screenshots_to_process:
                # Bulk delete option
                st.subheader("Bulk Delete Screenshots")
                if st.button("🗑️ Delete All Filtered Screenshots", type="secondary"):
                    with st.spinner("Deleting screenshots..."):
                        deleted_count = 0
                        for payment in screenshots_to_process:
                            if delete_screenshot_file(payment.get("screenshot")):
                                remove_screenshot_from_payment(payment.get("id"))
                                remove_screenshot_from_student(payment.get("student_id"))
                                deleted_count += 1
                        
                        st.success(f"Successfully deleted {deleted_count} screenshots!")
                        st.rerun()
                
                # View filtered payments
                st.subheader("Filtered Payments with Screenshots")
                for payment in screenshots_to_process[:10]:  # Show first 10
                    student = get_student_by_id(payment.get("student_id"))
                    if student:
                        with st.expander(f"{student.get('name')} - {payment.get('transaction_id')}"):
                            col_view, col_del = st.columns(2)
                            with col_view:
                                if st.button("👁️ View", key=f"bulk_view_{payment['id']}"):
                                    screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                                    if screenshot_path.exists():
                                        with open(screenshot_path, "rb") as f:
                                            img_bytes = f.read()
                                        st.image(img_bytes, caption="Payment Screenshot", use_column_width=True)
                            with col_del:
                                if st.button("🗑️ Delete", key=f"bulk_delete_{payment['id']}", type="secondary"):
                                    if delete_screenshot_file(payment.get("screenshot")):
                                        remove_screenshot_from_payment(payment.get("id"))
                                        remove_screenshot_from_student(payment.get("student_id"))
                                        st.success("Screenshot deleted!")
                                        st.rerun()
    
    with tab3:
        st.subheader("Screenshot Analytics")
        
        payments = get_payments()
        
        if payments:
            # Calculate statistics
            total_payments = len(payments)
            payments_with_screenshots = [p for p in payments if p.get("screenshot")]
            payments_without_screenshots = total_payments - len(payments_with_screenshots)
            deleted_screenshots = len([p for p in payments if p.get("screenshot_deleted")])
            active_screenshots = len(payments_with_screenshots) - deleted_screenshots
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Payments", total_payments)
            with col2:
                st.metric("With Screenshots", len(payments_with_screenshots))
            with col3:
                st.metric("Without Screenshots", payments_without_screenshots)
            
            col4, col5 = st.columns(2)
            with col4:
                st.metric("Active Screenshots", active_screenshots)
            with col5:
                st.metric("Deleted Screenshots", deleted_screenshots)
            
            # Pie chart for screenshot distribution
            st.divider()
            st.subheader("Screenshot Distribution")
            
            import plotly.express as px
            
            # Create data for pie chart
            labels = ['With Screenshots', 'Without Screenshots', 'Deleted Screenshots']
            values = [active_screenshots, payments_without_screenshots, deleted_screenshots]
            
            fig = px.pie(
                values=values,
                names=labels,
                title="Screenshot Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent screenshot activity
            st.divider()
            st.subheader("Recent Screenshot Activity")
            
            recent_payments_with_screenshots = sorted(
                [p for p in payments if p.get("screenshot")],
                key=lambda x: x.get("submission_date", ""),
                reverse=True
            )[:10]
            
            if recent_payments_with_screenshots:
                for payment in recent_payments_with_screenshots:
                    student = get_student_by_id(payment.get("student_id"))
                    if student:
                        col_status, col_name, col_date = st.columns([1, 3, 2])
                        with col_status:
                            if payment.get("screenshot_deleted"):
                                st.warning("🗑️")
                            else:
                                st.success("📸")
                        with col_name:
                            st.write(f"{student.get('name')} ({student.get('roll_number')})")
                        with col_date:
                            st.write(format_datetime(payment.get("submission_date")))
                        st.divider()

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
            
            # Convert to DataFrame with payment date
            df = pd.DataFrame([
                {
                    "Name": s.get("name"),
                    "Roll Number": s.get("roll_number"),
                    "Payment Status": s.get("payment_status"),
                    "Payment Date": format_datetime(s.get("payment_datetime", "")),
                    "Timestamp Type": "Auto" if s.get("auto_timestamp") else "Manual",
                    "Screenshot Status": "Deleted" if s.get("screenshot_deleted") else ("Available" if any(p.get("screenshot") for p in get_student_payments(s.get("id"))) else "Not Available"),
                    "Payment Account Used": s.get("payment_account_used", ""),
                    "Admin Remarks": s.get("admin_remarks", ""),
                    "Student Remarks": s.get("student_remarks", ""),
                    "Added By": "Admin" if s.get("added_by_admin") else "Student",
                    "Registration Date": format_datetime(s.get("registration_date", ""))
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
                        "Payment Date": format_datetime(payment.get("payment_datetime", "")),
                        "Timestamp Type": "Auto" if payment.get("auto_timestamp") else "Manual",
                        "Screenshot Status": "Deleted" if payment.get("screenshot_deleted") else ("Available" if payment.get("screenshot") else "Not Available"),
                        "Form Submission Date": format_datetime(payment.get("submission_date", "")),
                        "Payment Account": payment.get("payment_account", ""),
                        "Submitted By": "Admin" if payment.get("added_by_admin") else "Student",
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
            
            # Filter payments with active screenshots (not deleted)
            payments_with_screenshots = [p for p in filtered_payments if p.get("screenshot") and not p.get("screenshot_deleted")]
            
            if not payments_with_screenshots:
                st.warning("No active screenshots found for the selected filter")
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
                                new_name = f"{student.get('roll_number')}_{student.get('name')}_{payment.get('transaction_id')}_{payment.get('screenshot')}"
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
                st.metric("Total Amount Collected", f"PKR {total_amount:,}")
            with col2:
                st.metric("Total Paid Transactions", total_paid_count)
            with col3:
                avg_amount = total_amount / total_paid_count if total_paid_count > 0 else 0
                st.metric("Average Payment", f"PKR {avg_amount:,.2f}")
            
            # Screenshot analytics
            st.divider()
            st.subheader("Screenshot Analytics")
            
            payments_with_screenshots = len([p for p in payments if p.get("screenshot")])
            payments_without_screenshots = len(payments) - payments_with_screenshots
            deleted_screenshots = len([p for p in payments if p.get("screenshot_deleted")])
            active_screenshots = payments_with_screenshots - deleted_screenshots
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("With Screenshots", payments_with_screenshots)
            with col2:
                st.metric("Without Screenshots", payments_without_screenshots)
            with col3:
                st.metric("Deleted Screenshots", deleted_screenshots)
            
            # Recent activity
            st.divider()
            st.subheader("Recent Activity")
            
            recent_payments = sorted(payments, key=lambda x: x.get("payment_datetime", x.get("submission_date", "")), reverse=True)[:5]
            
            for payment in recent_payments:
                student = get_student_by_id(payment.get("student_id"))
                if student:
                    col1, col2, col3 = st.columns([3, 2, 2])
                    with col1:
                        st.write(f"**{student.get('name')}** ({student.get('roll_number')})")
                    with col2:
                        st.write(f"PKR {payment.get('amount')} - {payment.get('status')}")
                    with col3:
                        payment_date = format_datetime(payment.get("payment_datetime", payment.get("submission_date")))
                        st.write(f"{payment_date}")
                    st.divider()

def show_admin_settings():
    st.title("⚙️ Admin Settings")
    
    admin_data = get_admin_data()
    
    tab1, tab2 = st.tabs(["Change Credentials", "System Info"])
    
    with tab1:
        st.subheader("Change Username and Password")
        
        with st.form("change_credentials"):
            current_password = st.text_input("Current Password*", type="password")
            new_username = st.text_input("New Username*", value=admin_data.get("username", ""))
            new_password = st.text_input("New Password*", type="password")
            confirm_password = st.text_input("Confirm New Password*", type="password")
            
            if st.form_submit_button("💾 Update Credentials"):
                if not current_password or not new_username or not new_password or not confirm_password:
                    st.error("Please fill all required fields (*)")
                elif not authenticate(admin_data.get("username"), current_password):
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
                    st.rerun()
    
    with tab2:
        st.subheader("System Information")
        
        students = get_students()
        payments = get_payments()
        contact_info = get_contact_info()
        tab_visibility = get_tab_visibility()
        base_url = get_base_url()
        screenshot_settings = get_screenshot_settings()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"Total Students: {len(students)}")
            st.info(f"Total Payments: {len(payments)}")
            st.info(f"Payment Amount: PKR {admin_data.get('payment_amount', 5000)}")
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
            st.info(f"Auto Timestamps: {len([s for s in students if s.get('auto_timestamp')])}")
            st.info(f"Screenshot Download: {'Enabled' if screenshot_settings.get('allow_download') else 'Disabled'}")
            st.info(f"Screenshot Delete: {'Enabled' if screenshot_settings.get('allow_delete') else 'Disabled'}")
        
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
            st.markdown(f'<a href="{get_short_url()}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%;">🔗 Open Student Portal</button></a>', unsafe_allow_html=True)
        
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

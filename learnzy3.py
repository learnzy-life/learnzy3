import streamlit as st
import pandas as pd
import time
import random
import smtplib
from email.message import EmailMessage
import gspread
from google.oauth2.service_account import Credentials

# --- Configuration ---
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
SERVICE_ACCOUNT_FILE = 'service_account.json'  # Your service account credentials

# Google Sheets Configuration
DATA_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1qrdURj3XHZHStT2BG1ndmq0LyFHGbvVVQSruBlkH9mk/edit#gid=0'
MOCK_TEST_GIDS = {
    'Mock1': '848132391',
    'Mock2': '610172732',
    'Mock3': '1133755197',
    'Mock4': '690484996',
    'Mock5': '160639837'
}
RESULTS_SHEET_URL = 'your-results-sheet-url-here'  # For storing results

# Email Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = 'your-email@gmail.com'
EMAIL_PASSWORD = 'your-app-password'  # Use app-specific password

# --- Session State Initialization ---
required_states = {
    'authenticated': False,
    'current_mock': None,
    'test_started': False,
    'current_question': 0,
    'user_answers': {},
    'question_start_time': time.time(),
    'user_email': None,
    'verification_code': None,
    'code_verified': False
}

for key, value in required_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Helper Functions ---
def send_verification_code(email):
    """Send verification code to user's email"""
    code = str(random.randint(100000, 999999))
    st.session_state.verification_code = code
    
    msg = EmailMessage()
    msg['Subject'] = 'Your Verification Code'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = email
    msg.set_content(f'Your verification code is: {code}')
    
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def load_mock_test(mock_name):
    """Load specific mock test data"""
    gid = MOCK_TEST_GIDS[mock_name]
    url = f'https://docs.google.com/spreadsheets/d/1qrdURj3XHZHStT2BG1ndmq0LyFHGbvVVQSruBlkH9mk/export?format=csv&gid={gid}'
    return pd.read_csv(url).to_dict('records')

def save_to_gsheet(data):
    """Save results to Google Sheet"""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(RESULTS_SHEET_URL).sheet1
    sheet.append_row(data)

# --- Authentication Flow ---
def email_auth():
    """Handle email-based authentication"""
    with st.form("auth_form"):
        email = st.text_input("Enter your Gmail address")
        submitted = st.form_submit_button("Send Verification Code")
        
        if submitted:
            if '@gmail.com' in email:
                send_verification_code(email)
                st.session_state.user_email = email
                st.success("Verification code sent to your email!")
            else:
                st.error("Please enter a valid Gmail address")

    if st.session_state.user_email:
        with st.form("verify_form"):
            code = st.text_input("Enter verification code")
            if st.form_submit_button("Verify Code"):
                if code == st.session_state.verification_code:
                    st.session_state.authenticated = True
                    st.session_state.code_verified = True
                    st.rerun()
                else:
                    st.error("Invalid verification code")

# --- Mock Test Selection ---
def mock_test_selection():
    """Display mock test selection cards"""
    st.header("Available Mock Tests")
    cols = st.columns(3)
    
    mocks = list(MOCK_TEST_GIDS.keys())
    for idx, mock in enumerate(mocks):
        with cols[idx % 3]:
            with st.container(border=True):
                st.subheader(mock)
                if st.button(f"Select {mock}", key=mock):
                    st.session_state.current_mock = mock
                    st.rerun()

# --- Test Interface ---
def display_question(q):
    """Display question and handle navigation"""
    st.subheader(f"Question {st.session_state.current_question + 1} of {len(questions)}")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**{q['Question Text']}**")
        options = [q['Option A'], q['Option B'], q['Option C'], q['Option D']]
        answer = st.radio("Options:", options, key=f"q{st.session_state.current_question}")
    
    with col2:
        st.metric("Recommended Time", f"{q['Time to Solve (seconds)']}s")
        st.progress((time.time() - st.session_state.question_start_time) / q['Time to Solve (seconds)'])

    if st.button("Next ➡️"):
        process_answer(q, answer)
        if st.session_state.current_question < len(questions) - 1:
            st.session_state.current_question += 1
            st.session_state.question_start_time = time.time()
            st.rerun()
        else:
            st.session_state.test_started = False
            st.rerun()

def process_answer(q, answer):
    """Process and store user answers"""
    options = [q['Option A'], q['Option B'], q['Option C'], q['Option D']]
    selected_option = chr(65 + options.index(answer))
    
    result_data = {
        'user_email': st.session_state.user_email,
        'mock_test': st.session_state.current_mock,
        'question_id': q['Question Number'],
        'selected_answer': selected_option,
        'correct_answer': q['Correct Answer'],
        'time_taken': time.time() - st.session_state.question_start_time,
        'recommended_time': q['Time to Solve (seconds)'],
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    save_to_gsheet(list(result_data.values()))
    st.session_state.user_answers[q['Question Number']] = result_data

# --- Enhanced Analysis Report ---
def show_results():
    """Display enhanced analysis report"""
    st.balloons()
    st.title("Advanced Performance Analysis")
    
    # Calculate overall metrics
    total_time = sum(ans['time_taken'] for ans in st.session_state.user_answers.values())
    recommended_time = sum(ans['recommended_time'] for ans in st.session_state.user_answers.values())
    correct = sum(1 for ans in st.session_state.user_answers.values() if ans['selected_answer'] == ans['correct_answer'])
    accuracy = (correct / len(questions)) * 100

    # Main metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Score", f"{correct}/{len(questions)}")
    with col2:
        st.metric("Accuracy", f"{accuracy:.1f}%")
    with col3:
        st.metric("Time Efficiency", f"{(recommended_time/total_time)*100:.1f}%")

    # Detailed analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Subject Analysis", "⏱ Time Analysis", "🎯 Difficulty Breakdown", "📚 Learning Resources"])

    with tab1:
        subject_analysis()
    
    with tab2:
        time_analysis()
    
    with tab3:
        difficulty_analysis()
    
    with tab4:
        learning_resources()

def subject_analysis():
    """Subject-wise performance breakdown"""
    df = pd.DataFrame(st.session_state.user_answers.values())
    subject_groups = df.groupby('Subject')
    
    for subject, data in subject_groups:
        with st.expander(f"{subject} Analysis"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Accuracy Metrics")
                correct = sum(data['selected_answer'] == data['correct_answer'])
                acc = (correct / len(data)) * 100
                st.metric("Accuracy", f"{acc:.1f}%")
                st.progress(acc/100)
                
                st.write(f"**Topics Covered:** {', '.join(data['Topic'].unique())}")
            
            with col2:
                st.subheader("Time Management")
                avg_time = data['time_taken'].mean()
                rec_time = data['recommended_time'].mean()
                st.metric("Your Average Time", f"{avg_time:.1f}s")
                st.metric("Recommended Time", f"{rec_time:.1f}s")
                st.write(f"**Time Efficiency:** {(rec_time/avg_time)*100:.1f}%")

# ... (Similar functions for time_analysis, difficulty_analysis, learning_resources)

# --- Main App Flow ---
def main():
    st.title("📚 Smart Mock Test Platform 2.0")
    
    if not st.session_state.authenticated:
        email_auth()
    else:
        if not st.session_state.current_mock:
            mock_test_selection()
        elif not st.session_state.test_started:
            with st.popover(f"{st.session_state.current_mock} Syllabus"):
                st.write("Mock Test Syllabus Details Here...")
                if st.button("Start Test"):
                    st.session_state.test_started = True
                    st.rerun()
        else:
            global questions
            questions = load_mock_test(st.session_state.current_mock)
            
            if st.session_state.current_question < len(questions):
                display_question(questions[st.session_state.current_question])
            else:
                show_results()

if __name__ == "__main__":
    main()

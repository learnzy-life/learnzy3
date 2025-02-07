# mocktest_analysis.py
import streamlit as st
import pandas as pd
import time
import random
import smtplib
from email.message import EmailMessage
import gspread
from google.oauth2.service_account import Credentials

# ===== Configuration =====
# Google Sheets Setup
SERVICE_ACCOUNT_FILE = 'service_account.json'  # Create this file from Google Cloud credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

MOCK_TEST_DATA = {
    'Mock1': {'gid': '848132391'},
    'Mock2': {'gid': '610172732'},
    'Mock3': {'gid': '1133755197'},
    'Mock4': {'gid': '690484996'},
    'Mock5': {'gid': '160639837'}
}

RESULTS_SHEET_URL = 'your-results-sheet-url'  # Replace with your results sheet URL

# Email Configuration (Use App Password)
SMTP_CONFIG = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'sender_email': 'your-email@gmail.com',
    'password': 'your-app-password'  # Enable 2FA and create app password
}

# Initialize Session State
if 'auth' not in st.session_state:
    st.session_state.auth = {
        'authenticated': False,
        'email': None,
        'code': None,
        'verified': False
    }

if 'test' not in st.session_state:
    st.session_state.test = {
        'current_mock': None,
        'started': False,
        'current_question': 0,
        'answers': {},
        'start_time': None
    }

# ===== Helper Functions =====
def send_verification_email(receiver_email):
    """Send 6-digit verification code to user's email"""
    code = str(random.randint(100000, 999999))
    st.session_state.auth['code'] = code
    
    msg = EmailMessage()
    msg['Subject'] = 'Your Verification Code'
    msg['From'] = SMTP_CONFIG['sender_email']
    msg['To'] = receiver_email
    msg.set_content(f'''
        Your verification code is: {code}
        This code will expire in 5 minutes.
    ''')

    try:
        with smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port']) as server:
            server.starttls()
            server.login(SMTP_CONFIG['sender_email'], SMTP_CONFIG['password'])
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

def load_mock_test(mock_name):
    """Load selected mock test from Google Sheets"""
    try:
        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        
        sheet = client.open_by_url(MOCK_TEST_DATA[mock_name]['url'])
        worksheet = sheet.get_worksheet_by_id(int(MOCK_TEST_DATA[mock_name]['gid']))
        return worksheet.get_all_records()
    except Exception as e:
        st.error(f"Error loading mock test: {str(e)}")
        return []

def save_results_to_gsheet(results):
    """Save user results to Google Sheet"""
    try:
        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, 
            scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        sheet = client.open_by_url(RESULTS_SHEET_URL).sheet1
        sheet.append_row(results)
    except Exception as e:
        st.error(f"Failed to save results: {str(e)}")

# ===== Authentication Flow =====
def email_authentication():
    """Handle email-based authentication flow"""
    with st.container(border=True):
        st.header("Login with Email")
        
        if not st.session_state.auth['verified']:
            email = st.text_input("Enter your Gmail address")
            if st.button("Send Verification Code"):
                if '@gmail.com' in email:
                    if send_verification_email(email):
                        st.session_state.auth['email'] = email
                        st.success("Verification code sent!")
                else:
                    st.error("Please enter a valid Gmail address")

        if st.session_state.auth['email']:
            code = st.text_input("Enter 6-digit code")
            if st.button("Verify Code"):
                if code == st.session_state.auth['code']:
                    st.session_state.auth['authenticated'] = True
                    st.session_state.auth['verified'] = True
                    st.rerun()
                else:
                    st.error("Invalid verification code")

# ===== Test Interface =====
def mock_test_selection():
    """Display mock test selection cards"""
    st.header("Available Mock Tests")
    cols = st.columns(3)
    
    for idx, mock in enumerate(MOCK_TEST_DATA.keys()):
        with cols[idx % 3]:
            with st.container(border=True):
                st.subheader(mock)
                if st.button(f"Select {mock}"):
                    st.session_state.test['current_mock'] = mock

def display_question(question):
    """Display question and handle navigation"""
    q = question
    time_limit = q['Time to Solve (seconds)']
    elapsed_time = time.time() - st.session_state.test['start_time']
    
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"Question {st.session_state.test['current_question'] + 1}")
            st.markdown(f"**{q['Question Text']}**")
            answer = st.radio("Options:", 
                            [q['Option A'], q['Option B'], 
                             q['Option C'], q['Option D']],
                            key=f"q{st.session_state.test['current_question']}")
        
        with col2:
            st.metric("Recommended Time", f"{time_limit}s")
            st.progress(min(elapsed_time / time_limit, 1.0))
            
            if st.button("Next ➡️"):
                process_answer(q, answer)
                if st.session_state.test['current_question'] < len(questions) - 1:
                    st.session_state.test['current_question'] += 1
                    st.session_state.test['start_time'] = time.time()
                    st.rerun()
                else:
                    st.session_state.test['started'] = False
                    st.rerun()

def process_answer(question, answer):
    """Process and store user answer"""
    options = [question['Option A'], question['Option B'],
               question['Option C'], question['Option D']]
    selected_option = chr(65 + options.index(answer))
    
    result = {
        'email': st.session_state.auth['email'],
        'mock_test': st.session_state.test['current_mock'],
        'question_id': question['Question Number'],
        'selected': selected_option,
        'correct': question['Correct Answer'],
        'time_spent': time.time() - st.session_state.test['start_time'],
        'recommended_time': question['Time to Solve (seconds)'],
        'difficulty': question['Difficulty Level'],
        'subject': question['Subject'],
        'topic': question['Topic'],
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    save_results_to_gsheet(list(result.values()))
    st.session_state.test['answers'][question['Question Number']] = result

# ===== Enhanced Analysis Report =====
def generate_analysis():
    """Generate comprehensive analysis report"""
    st.balloons()
    st.title("Advanced Performance Report")
    
    # Convert answers to DataFrame
    df = pd.DataFrame(st.session_state.test['answers'].values())
    
    # Overall Metrics
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Score", f"{sum(df['selected'] == df['correct'])}/{len(df)}")
        with col2:
            accuracy = (sum(df['selected'] == df['correct']) / len(df)) * 100
            st.metric("Overall Accuracy", f"{accuracy:.1f}%")
        with col3:
            time_ratio = (df['recommended_time'].sum() / df['time_spent'].sum()) * 100
            st.metric("Time Efficiency", f"{time_ratio:.1f}%")
    
    # Tabs for Detailed Analysis
    tab1, tab2, tab3 = st.tabs(["📈 Subject Analysis", "⏱ Time Management", "🎯 Recommendations"])
    
    with tab1:
        st.header("Subject-wise Performance")
        subjects = df.groupby('subject')
        for name, group in subjects:
            with st.expander(f"{name} Analysis"):
                cols = st.columns(2)
                with cols[0]:
                    st.subheader("Accuracy")
                    correct = sum(group['selected'] == group['correct'])
                    st.metric(f"Correct Answers", f"{correct}/{len(group)}")
                    st.progress(correct/len(group))
                
                with cols[1]:
                    st.subheader("Time Comparison")
                    avg_time = group['time_spent'].mean()
                    rec_time = group['recommended_time'].mean()
                    st.metric("Your Average Time", f"{avg_time:.1f}s")
                    st.metric("Recommended Average Time", f"{rec_time:.1f}s")
    
    with tab2:
        st.header("Time Management Analysis")
        df['time_diff'] = df['time_spent'] - df['recommended_time']
        st.bar_chart(df.set_index('question_id')[['time_spent', 'recommended_time']])
        
        with st.expander("Time Distribution"):
            st.write("Questions where you took extra time:")
            late_questions = df[df['time_diff'] > 0]
            st.dataframe(late_questions[['question_id', 'subject', 'time_diff']])
    
    with tab3:
        st.header("Personalized Recommendations")
        difficulty_groups = df.groupby('difficulty')
        for level, group in difficulty_groups:
            accuracy = (sum(group['selected'] == group['correct']) / len(group)) * 100
            if accuracy < 60:
                st.warning(f"**{level} Level Questions**: Need improvement ({accuracy:.1f}% accuracy)")
                st.write(f"Suggested resources: [Practice {level} {group.iloc[0]['subject']} Questions](https://example.com)")
            else:
                st.success(f"**{level} Level Questions**: Strong performance ({accuracy:.1f}% accuracy)")
        
        st.divider()
        st.subheader("Priority Areas")
        weak_topics = df[df['selected'] != df['correct']]['topic'].value_counts()
        st.write(weak_topics)

# ===== Main App Flow =====
def main():
    st.set_page_config(page_title="Smart Mock Test Platform", layout="wide")
    
    if not st.session_state.auth['authenticated']:
        email_authentication()
    else:
        st.header(f"Welcome, {st.session_state.auth['email']}")
        
        if not st.session_state.test['current_mock']:
            mock_test_selection()
        elif not st.session_state.test['started']:
            with st.popover("Mock Test Syllabus", use_container_width=True):
                st.write(f"### {st.session_state.test['current_mock']} Syllabus")
                st.write("""
                - Topic 1: Fundamental Concepts
                - Topic 2: Advanced Applications
                - Topic 3: Problem Solving Techniques
                """)
                if st.button("Start Test"):
                    st.session_state.test['started'] = True
                    global questions
                    questions = load_mock_test(st.session_state.test['current_mock'])
                    st.session_state.test['start_time'] = time.time()
                    st.rerun()
        else:
            if st.session_state.test['current_question'] < len(questions):
                display_question(questions[st.session_state.test['current_question']])
            else:
                generate_analysis()
                if st.button("Retake Test"):
                    st.session_state.test = {
                        'current_mock': None,
                        'started': False,
                        'current_question': 0,
                        'answers': {},
                        'start_time': None
                    }
                    st.rerun()

if __name__ == "__main__":
    main()

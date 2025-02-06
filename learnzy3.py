import streamlit as st
import pandas as pd
import hashlib
import time
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets Configuration
scope = ["https://spreadsheets.google.com/feeds", 
         "https://www.googleapis.com/auth/drive"]

# Load credentials from secrets (you need to create these in Streamlit secrets)
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
gc = gspread.authorize(credentials)

# User data spreadsheet
USER_SHEET = gc.open_by_url("https://docs.google.com/spreadsheets/d/14ytB5rB0VAMgzsoflLujEMcsnv5HKTj2VKzTPuAoZTI/edit#gid=0")
RESPONSE_SHEET = gc.open_by_url("https://docs.google.com/spreadsheets/d/14ytB5rB0VAMgzsoflLujEMcsnv5HKTj2VKzTPuAoZTI/edit#gid=0")

# Configure page
st.set_page_config(
    page_title="NEET Mock Tests",
    page_icon="🧪",
    layout="centered"
)

# Mock Test Configuration (Update GIDs with actual sheet IDs)
MOCK_TESTS = {
    "Mock Test 1": {"gid": "0", "syllabus": "Biology (10), Physics (10), Chemistry (10)"},
    "Mock Test 2": {"gid": "ADD_GID", "syllabus": "..."},
    "Mock Test 3": {"gid": "ADD_GID", "syllabus": "..."},
    "Mock Test 4": {"gid": "ADD_GID", "syllabus": "..."},
    "Mock Test 5": {"gid": "ADD_GID", "syllabus": "..."}
}

COLUMN_MAP = {
    "Question Number": "id",
    "Question Text": "text",
    "Option A": "A",
    "Option B": "B",
    "Option C": "C",
    "Option D": "D",
    "Correct Answer": "correct",
    "Topic": "topic",
    "Subtopic": "subtopic",
    "Difficulty Level": "difficulty",
    "Time to Solve": "ideal_time",
}

def init_session():
    required_states = {
        'authenticated': False,
        'current_test': None,
        'questions': [],
        'user_answers': {},
        'current_question': 0,
        'show_report': False,
        'reset_password': False,
        'current_user': None
    }
    for key, val in required_states.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

@st.cache_data(ttl=3600)
def load_questions(gid):
    try:
        sheet = USER_SHEET.get_worksheet_by_id(gid)
        df = pd.DataFrame(sheet.get_all_records()).rename(columns=COLUMN_MAP)
        
        required_cols = ['id', 'text', 'A', 'B', 'C', 'D', 'correct']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
            return []
        
        try:
            df['ideal_time'] = pd.to_numeric(df['ideal_time'], errors='coerce').fillna(60) * 60
        except KeyError:
            df['ideal_time'] = 60
            
        return df.to_dict('records')
    
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return []

def get_user_db():
    try:
        return USER_SHEET.worksheet("users").get_all_records()
    except:
        return []

def save_user(email, password_hash):
    try:
        worksheet = USER_SHEET.worksheet("users")
        worksheet.append_row([email, password_hash, "", ""])
        return True
    except Exception as e:
        st.error(f"Failed to save user: {str(e)}")
        return False

def save_responses(email, test_name, responses):
    try:
        worksheet = RESPONSE_SHEET.worksheet("responses")
        for qid, data in responses.items():
            row = [
                email,
                test_name,
                qid,
                data['selected'],
                data['correct'],
                data['time_taken'],
                data.get('error_type', ''),
                ",".join(data.get('triggers', [])),
                time.strftime("%Y-%m-%d %H:%M:%S")
            ]
            worksheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Failed to save responses: {str(e)}")
        return False

def auth_system():
    if not st.session_state.authenticated:
        st.title("NEET Mock Test Platform")
        
        if st.session_state.reset_password:
            with st.form("Password Reset"):
                email = st.text_input("Registered Email")
                if st.form_submit_button("Send Reset Link"):
                    users = get_user_db()
                    if any(u['email'] == email for u in users):
                        st.info("Password reset link sent to your email (simulated)")
                    else:
                        st.error("Email not found")
                    st.session_state.reset_password = False
                if st.button("Back to Login"):
                    st.session_state.reset_password = False
            return

        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            with st.form("Login"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    users = get_user_db()
                    user = next((u for u in users if u['email'] == email), None)
                    if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
                        st.session_state.authenticated = True
                        st.session_state.current_user = email
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                st.markdown("[Forgot password?](#reset)")

        with tab2:
            with st.form("Sign Up"):
                new_email = st.text_input("Email")
                new_pass = st.text_input("Password", type="password")
                confirm_pass = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account"):
                    if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
                        st.error("Invalid email format")
                    elif new_pass != confirm_pass:
                        st.error("Passwords don't match")
                    elif any(u['email'] == new_email for u in get_user_db()):
                        st.error("Email already exists")
                    else:
                        if save_user(new_email, hashlib.sha256(new_pass.encode()).hexdigest()):
                            st.success("Account created! Please login")
                        else:
                            st.error("Registration failed")

        if st.markdown("Forgot password? [Click here](#reset)"):
            st.session_state.reset_password = True
            st.rerun()

def test_interface():
    if st.session_state.questions:
        q = st.session_state.questions[st.session_state.current_question]
        
        st.progress((st.session_state.current_question + 1)/len(st.session_state.questions))
        st.subheader(f"Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}")
        st.markdown(f"**{q['text']}**")
        
        options = [q['A'], q['B'], q['C'], q['D']]
        answer = st.radio("Select your answer:", options, key=f"q_{q['id']}")
        
        cols = st.columns([1, 3, 1])
        with cols[0]:
            if st.button("← Back", disabled=st.session_state.current_question == 0):
                st.session_state.current_question -= 1
                st.rerun()
        
        with cols[2]:
            btn_label = "Next →" if st.session_state.current_question < len(st.session_state.questions)-1 else "Submit"
            if st.button(btn_label):
                selected = ['A', 'B', 'C', 'D'][options.index(answer.strip())]
                st.session_state.user_answers[q['id']] = {
                    'selected': selected,
                    'correct': q['correct'].strip().upper(),
                    'time_taken': time.time() - st.session_state.get('q_start_time', time.time()),
                    'question_text': q['text']
                }
                st.session_state.q_start_time = time.time()
                
                if st.session_state.current_question < len(st.session_state.questions)-1:
                    st.session_state.current_question += 1
                else:
                    handle_test_completion()
                st.rerun()
        
        show_time_tracker(q.get('ideal_time', 60))
    else:
        st.error("Failed to load questions. Please try again later.")

def show_time_tracker(ideal_time):
    current_time = time.time() - st.session_state.get('q_start_time', time.time())
    cols = st.columns(2)
    cols[0].metric("Your Time", f"{int(current_time)}s")
    cols[1].metric("Ideal Time", f"{int(ideal_time)}s")
    st.progress(min(current_time/ideal_time, 1.0))

def handle_test_completion():
    st.session_state.show_report = True
    if save_responses(st.session_state.current_user, 
                     st.session_state.current_test,
                     st.session_state.user_answers):
        st.success("Test results saved!")
    else:
        st.error("Failed to save test results")

def generate_report():
    st.title("📊 Test Report")
    
    total_score = sum(4 if ans['selected'] == ans['correct'] else -1 
                     for ans in st.session_state.user_answers.values())
    st.header(f"Total Score: {total_score}")
    
    with st.expander("Detailed Analysis"):
        st.subheader("Time Management")
        total_time = sum(ans['time_taken'] for ans in st.session_state.user_answers.values())
        ideal_time = sum(q.get('ideal_time', 60) for q in st.session_state.questions)
        cols = st.columns(2)
        cols[0].metric("Your Time", f"{int(total_time//60)}m {int(total_time%60)}s")
        cols[1].metric("Ideal Time", f"{int(ideal_time//60)}m {int(ideal_time%60)}s")
        
        st.subheader("Error Analysis")
        wrong_answers = [ans for ans in st.session_state.user_answers.values() 
                        if ans['selected'] != ans['correct']]
        if wrong_answers:
            for ans in wrong_answers:
                with st.expander(f"Question {ans['question_text'][:50]}..."):
                    st.write(f"**Your Answer:** {ans['selected']}")
                    st.write(f"**Correct Answer:** {ans['correct']}")
        else:
            st.success("No errors! Perfect score!")

    if st.button("Return to Dashboard"):
        st.session_state.current_test = None
        st.session_state.show_report = False
        st.rerun()

def main():
    auth_system()
    
    if st.session_state.authenticated:
        if not st.session_state.current_test:
            st.title("Available Mock Tests")
            for test_name, details in MOCK_TESTS.items():
                with st.expander(f"{test_name} - {details['syllabus']}"):
                    if st.button(f"Start {test_name}"):
                        questions = load_questions(details['gid'])
                        if questions:
                            st.session_state.current_test = test_name
                            st.session_state.questions = questions
                            st.session_state.user_answers = {}
                            st.session_state.current_question = 0
                            st.session_state.q_start_time = time.time()
                        else:
                            st.error("Failed to load questions")
                        st.rerun()
        
        elif st.session_state.current_test:
            if st.session_state.show_report:
                generate_report()
            else:
                test_interface()

if __name__ == "__main__":
    main()

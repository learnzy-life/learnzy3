import streamlit as st
import pandas as pd
import hashlib
import time
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="NEET Mock Tests",
    page_icon="🧪",
    layout="centered"
)

# Google Sheet configuration
SHEET_BASE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQU0OgpQOjfuOoscCzEGqLWkAvsSFNXSNYCIwCSDWUYHUFmdWuvMUO1nj8HaF86J89SQ9-udMNkq2kI/pub?output=csv"
MOCK_TESTS = {
    "Mock Test 1": {"gid": "319338355", "syllabus": "Biology (15), Physics (7), Chemistry (8)"},
    "Mock Test 2": {"gid": "0", "syllabus": "Biology (12), Physics (9), Chemistry (9)"},
    # Add remaining tests with actual gids
}

# Column mapping
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
    "Error Type": "error_type",
    "Self Assessed Triggers": "triggers"
}

# Session state management
def init_session():
    defaults = {
        'authenticated': False,
        'current_test': None,
        'questions': [],
        'user_answers': {},
        'current_question': 0,
        'show_report': False,
        'users': {}
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# Data loading
@st.cache_data(ttl=3600)
def load_questions(gid):
    try:
        url = f"{SHEET_BASE}&gid={gid}"
        df = pd.read_csv(url).rename(columns=COLUMN_MAP)
        
        # Validate columns
        required = list(COLUMN_MAP.values())[:10]  # First 10 are mandatory
        missing = [col for col in required if col not in df.columns]
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
            return []
        
        # Convert time to seconds
        df['ideal_time'] = df['ideal_time'] * 60  # Convert minutes to seconds
        return df.to_dict('records')
    
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return []

# Authentication system
def auth_system():
    with st.container():
        if not st.session_state.authenticated:
            tab1, tab2 = st.tabs(["Login", "Sign Up"])
            
            with tab1:
                with st.form("Login"):
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    if st.form_submit_button("Login"):
                        user = st.session_state.users.get(email)
                        if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
                            st.session_state.authenticated = True
                            st.session_state.current_user = email
                            st.rerun()
                        else:
                            st.error("Invalid credentials")

            with tab2:
                with st.form("Sign Up"):
                    new_email = st.text_input("Email")
                    new_pass = st.text_input("Password", type="password")
                    confirm_pass = st.text_input("Confirm Password", type="password")
                    if st.form_submit_button("Create Account"):
                        if new_pass != confirm_pass:
                            st.error("Passwords don't match")
                        elif new_email in st.session_state.users:
                            st.error("Email already exists")
                        else:
                            st.session_state.users[new_email] = {
                                'password': hashlib.sha256(new_pass.encode()).hexdigest(),
                                'progress': {},
                                'responses': {}
                            }
                            st.success("Account created! Please login")

# Test interface
def show_question(q):
    st.subheader(f"Question {st.session_state.current_question + 1}/{len(st.session_state.questions)}")
    st.markdown(f"**{q['text']}**")
    
    answer = st.radio("Options:", 
                     [q['A'], q['B'], q['C'], q['D']],
                     key=f"q_{q['id']}")
    
    cols = st.columns([1, 3, 1])
    with cols[0]:
        if st.button("← Back", disabled=st.session_state.current_question == 0):
            st.session_state.current_question -= 1
            st.rerun()
    
    with cols[2]:
        btn_label = "Next →" if st.session_state.current_question < len(st.session_state.questions)-1 else "Submit"
        if st.button(btn_label):
            record_answer(q, answer)
            if st.session_state.current_question < len(st.session_state.questions)-1:
                st.session_state.current_question += 1
            else:
                handle_test_completion()
            st.rerun()
    
    show_time_tracker(q['ideal_time'])

def record_answer(q, answer):
    selected = ['A', 'B', 'C', 'D'][[q['A'], q['B'], q['C'], q['D']].index(answer)]
    st.session_state.user_answers[q['id']] = {
        'selected': selected,
        'correct': q['correct'],
        'time_taken': time.time() - st.session_state.get('q_start_time', time.time()),
        'question_text': q['text']
    }
    st.session_state.q_start_time = time.time()

def show_time_tracker(ideal_time):
    current_time = time.time() - st.session_state.get('q_start_time', time.time())
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Your Time", f"{int(current_time)}s")
    with col2:
        st.metric("Ideal Time", f"{int(ideal_time)}s")
    st.progress(min(current_time/ideal_time, 1.0))

# Error tagging
def error_analysis():
    st.header("Error Analysis")
    wrong_answers = {k:v for k,v in st.session_state.user_answers.items() if v['selected'] != v['correct']}
    
    for qid, ans in wrong_answers.items():
        with st.expander(f"Question {qid}", expanded=True):
            st.write(ans['question_text'])
            ans['error_type'] = st.selectbox(
                "Error Type",
                ["Conceptual", "Silly Mistake", "Unprepared"],
                key=f"err_{qid}"
            )
            ans['triggers'] = st.multiselect(
                "Self Assessed Triggers",
                ["Time Pressure", "Topic Insecurity", "Ambiguity Fear", 
                 "Numerical Phobia", "Memory Gaps", "Past Trauma"],
                key=f"trig_{qid}"
            )
    
    if st.button("Generate Final Report"):
        st.session_state.show_report = True
        st.rerun()

# Reporting system
def generate_report():
    total_score = sum(4 if ans['selected'] == ans['correct'] else -1 
                     for ans in st.session_state.user_answers.values())
    
    total_time = sum(ans['time_taken'] for ans in st.session_state.user_answers.values())
    ideal_time = sum(q['ideal_time'] for q in st.session_state.questions)
    
    st.title("📊 Test Report")
    st.header(f"Score: {total_score}/{4*len(st.session_state.questions)}")
    
    with st.expander("Time Analysis", expanded=True):
        cols = st.columns(2)
        cols[0].metric("Your Total Time", f"{int(total_time//60)}m {int(total_time%60)}s")
        cols[1].metric("Recommended Time", f"{int(ideal_time//60)}m {int(ideal_time%60)}s")
        st.write(f"**Time Difference:** {int((total_time-ideal_time)//60)}m {int((total_time-ideal_time)%60)}s")
    
    with st.expander("Error Analysis"):
        error_counts = {}
        for ans in st.session_state.user_answers.values():
            if ans['selected'] != ans['correct']:
                et = ans.get('error_type', 'Not specified')
                error_counts[et] = error_counts.get(et, 0) + 1
        st.bar_chart(error_counts)
    
    if st.button("Return to Dashboard"):
        st.session_state.current_test = None
        st.session_state.show_report = False
        st.rerun()

# Main app flow
def main():
    auth_system()
    
    if st.session_state.authenticated:
        if not st.session_state.current_test:
            st.title("Available Mock Tests")
            for test_name, details in MOCK_TESTS.items():
                with st.expander(test_name):
                    st.write(f"**Syllabus:** {details['syllabus']}")
                    st.write("Contains 30 carefully curated questions")
                    if st.button(f"Start {test_name}"):
                        st.session_state.current_test = test_name
                        st.session_state.questions = load_questions(details['gid'])
                        st.session_state.user_answers = {}
                        st.session_state.current_question = 0
                        st.session_state.q_start_time = time.time()
                        st.rerun()
        
        elif st.session_state.questions:
            if not st.session_state.show_report:
                if st.session_state.current_question < len(st.session_state.questions):
                    show_question(st.session_state.questions[st.session_state.current_question])
                else:
                    error_analysis()
            else:
                generate_report()

if __name__ == "__main__":
    main()

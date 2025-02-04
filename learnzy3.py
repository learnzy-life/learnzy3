import streamlit as st
import pandas as pd
import time
import json
import firebase_admin
from firebase_admin import credentials, auth, firestore
from firebase_admin.exceptions import FirebaseError
from streamlit.components.v1 import html
from datetime import datetime

# Firebase Configuration
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

firebase_config = {
    "apiKey": "AIzaSyCLc4MGAeqehNLIGmLOtK3TA6fX1ftfkfA",
    "authDomain": "learnzy3.firebaseapp.com",
    "projectId": "learnzy3",
    "storageBucket": "learnzy3.firebasestorage.app",
    "messagingSenderId": "782772780808",
    "appId": "1:782772780808:web:d458e2fc0bb5468fc1b6bd",
    "measurementId": "G-Q5E06GFKNC"
}

# Google Sheets Configuration
SHEET_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR4BK9IQmKNdiw3Gx_BLj_3O_uAKmt4SSEwmqzGldFu0DhMnKQ4QGOZZQ1AsY-6AbbHgAGjs5H_gIuV/pub?output=csv'

# Session State Initialization
session_defaults = {
    'user': None,
    'current_test': None,
    'test_started': False,
    'questions': [],
    'test_data': {
        'score': 0,
        'responses': {},
        'start_time': None,
        'current_question': 0
    }
}

for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Firebase Auth Component
def firebase_login():
    firebase_config_json = json.dumps(firebase_config)
    
    login_js = f"""
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-auth.js"></script>
    <script>
        const firebaseConfig = {firebase_config_json};
        firebase.initializeApp(firebaseConfig);
        
        async function signInWithGoogle() {{
            const provider = new firebase.auth.GoogleAuthProvider();
            try {{
                const result = await firebase.auth().signInWithPopup(provider);
                const user = result.user;
                const token = await user.getIdToken();
                window.parent.postMessage({{"type": "user_token", "token": token}}, "*");
            }} catch (error) {{
                console.error(error);
            }}
        }}
    </script>
    <button onclick="signInWithGoogle()" style="padding: 10px 20px; background-color: #4285F4; color: white; border: none; border-radius: 5px; cursor: pointer;">
        Sign in with Google
    </button>
    """
    html(login_js, height=100)

# Data Loading with Validation
@st.cache_data(ttl=3600)
def load_questions():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        
        required_columns = [
            'Question ID', 'Question Text', 'Option A', 'Option B',
            'Option C', 'Option D', 'Correct Answer', 'Subject', 'Topic',
            'Sub- Topic', 'Difficulty Level', 'Question Type', 'Cognitive Level'
        ]
        
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"Missing columns: {', '.join(missing)}")
            return []
            
        valid_questions = []
        for _, row in df.iterrows():
            if all(row[['Option A', 'Option B', 'Option C', 'Option D', 'Correct Answer']].notna()):
                valid_questions.append(row.to_dict())
        
        return valid_questions[:30]  # First 30 questions for mock test
        
    except Exception as e:
        st.error(f"Data loading failed: {str(e)}")
        return []

# Test Management Functions
def initialize_test(test_number):
    st.session_state.test_data = {
        'score': 0,
        'responses': {},
        'start_time': time.time(),
        'current_question': 0
    }
    st.session_state.questions = load_questions()
    st.session_state.current_test = test_number
    st.session_state.test_started = True

def save_test_progress():
    if st.session_state.user:
        test_ref = db.collection('users').document(st.session_state.user['uid'])\
                   .collection('tests').document(f"test_{st.session_state.current_test}")
        
        test_data = {
            'score': st.session_state.test_data['score'],
            'progress': len(st.session_state.test_data['responses']),
            'timestamp': firestore.SERVER_TIMESTAMP,
            **st.session_state.test_data
        }
        test_ref.set(test_data, merge=True)

def complete_test():
    if st.session_state.user:
        test_ref = db.collection('users').document(st.session_state.user['uid'])\
                   .collection('tests').document(f"test_{st.session_state.current_test}")
        
        final_data = {
            'completed': True,
            'total_time': time.time() - st.session_state.test_data['start_time'],
            'final_score': st.session_state.test_data['score'],
            'responses': st.session_state.test_data['responses'],
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        test_ref.set(final_data, merge=True)
        
    st.session_state.test_started = False
    st.session_state.current_test = None

# Analytics Functions
def calculate_insights():
    responses = st.session_state.test_data['responses']
    
    insights = {
        'accuracy': (sum(1 for r in responses.values() if r['correct']) / len(responses)) * 100,
        'time_per_question': sum(r['time_spent'] for r in responses.values()) / len(responses),
        'topic_breakdown': {},
        'score_progression': []
    }
    
    for response in responses.values():
        topic = response['topic']
        if topic not in insights['topic_breakdown']:
            insights['topic_breakdown'][topic] = {'correct': 0, 'total': 0}
        insights['topic_breakdown'][topic]['total'] += 1
        insights['topic_breakdown'][topic]['correct'] += 1 if response['correct'] else 0
    
    return insights

def get_comparative_data():
    if st.session_state.user:
        tests_ref = db.collection('users').document(st.session_state.user['uid']).collection('tests')
        return [doc.to_dict() for doc in tests_ref.stream()]
    return []

# UI Components
def show_dashboard():
    st.header(f"Welcome, {st.session_state.user['name']}!")
    st.subheader("Available Mock Tests")
    
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.image("https://via.placeholder.com/150", width=100)
            if st.button(f"Test {i+1}", key=f"test_{i}"):
                st.session_state.current_test = i+1

def show_syllabus():
    st.subheader(f"Test {st.session_state.current_test} Syllabus")
    with st.expander("View Syllabus Details", expanded=True):
        st.write("""
        ### Mathematics (30 Questions)
        - Algebra: 10 questions
        - Geometry: 8 questions
        - Calculus: 12 questions
        """)
        st.write("**Time Limit:** 30 minutes")
        st.write("**Scoring:** +4 for correct, -1 for incorrect")
    
    if st.button("Start Test Now", type="primary"):
        initialize_test(st.session_state.current_test)

def show_question():
    q_idx = st.session_state.test_data['current_question']
    question = st.session_state.questions[q_idx]
    
    st.subheader(f"Question {q_idx+1}/30")
    st.markdown(f"**{question['Question Text']}**")
    
    options = {
        'A': question['Option A'],
        'B': question['Option B'],
        'C': question['Option C'],
        'D': question['Option D']
    }
    
    selected = st.radio("Options", list(options.values()), key=f"q_{q_idx}")
    
    if st.button("Next Question"):
        process_answer(question, options, selected)

def process_answer(question, options, selected):
    # Calculate time spent
    time_spent = time.time() - st.session_state.test_data['start_time']
    
    # Find selected key
    selected_key = [k for k, v in options.items() if v == selected][0]
    is_correct = selected_key == question['Correct Answer'].strip().upper()
    
    # Update score
    score_delta = 4 if is_correct else -1
    st.session_state.test_data['score'] += score_delta
    
    # Store response
    st.session_state.test_data['responses'][question['Question ID']] = {
        'question': question['Question Text'],
        'topic': question['Topic'],
        'subtopic': question['Sub- Topic'],
        'selected': selected_key,
        'correct': is_correct,
        'time_spent': time_spent
    }
    
    # Move to next question or complete
    if st.session_state.test_data['current_question'] < 29:
        st.session_state.test_data['current_question'] += 1
        st.session_state.test_data['start_time'] = time.time()
        save_test_progress()
        st.rerun()
    else:
        complete_test()
        st.rerun()

def show_results():
    insights = calculate_insights()
    
    st.header("Test Results Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Final Score", insights['accuracy'])
    col2.metric("Average Time/Question", f"{insights['time_per_question']:.1f}s")
    col3.metric("Total Time Taken", 
               f"{(time.time() - st.session_state.test_data['start_time'])/60:.1f} mins")
    
    st.subheader("Topic-wise Performance")
    for topic, data in insights['topic_breakdown'].items():
        accuracy = (data['correct'] / data['total']) * 100
        st.write(f"**{topic}**")
        st.progress(accuracy/100)
        st.caption(f"{data['correct']}/{data['total']} correct ({accuracy:.1f}%)")
    
    show_comparative_analysis()

def show_comparative_analysis():
    st.header("📈 Historical Performance")
    previous_tests = get_comparative_data()
    
    if len(previous_tests) > 1:
        df = pd.DataFrame({
            'Test': [f"Test {i+1}" for i in range(len(previous_tests))],
            'Score': [t['final_score'] for t in previous_tests],
            'Accuracy': [t['final_score']/(4*30)*100 for t in previous_tests]
        })
        
        st.subheader("Score Trend")
        st.line_chart(df.set_index('Test')['Accuracy'])
        
        st.subheader("Time Efficiency Improvement")
        st.bar_chart(df.set_index('Test')['Score'])
    else:
        st.info("Complete more tests to unlock comparative analysis!")

# Main App Flow
def main():
    st.set_page_config(page_title="Learnzy", layout="wide")
    
    # Authentication Flow
    if not st.session_state.user:
        st.title("Welcome to Learnzy! 📚")
        firebase_login()
        
        query_params = st.experimental_get_query_params()
        if 'token' in query_params:
            try:
                decoded_token = auth.verify_id_token(query_params['token'][0])
                st.session_state.user = {
                    'uid': decoded_token['uid'],
                    'name': decoded_token.get('name', 'User'),
                    'email': decoded_token.get('email', '')
                }
                st.rerun()
            except FirebaseError as e:
                st.error(f"Authentication failed: {str(e)}")
        return
    
    # Main Interface
    if st.session_state.test_started:
        # Timer Display
        elapsed_time = time.time() - st.session_state.test_data['start_time']
        time_left = max(1800 - elapsed_time, 0)
        mins, secs = divmod(time_left, 60)
        st.sidebar.progress(time_left/1800, text=f"Time Left: {int(mins):02d}:{int(secs):02d}")
        
        if time_left <= 0:
            complete_test()
            st.rerun()
        
        # Question Interface
        show_question()
    elif st.session_state.current_test:
        show_syllabus()
    else:
        show_dashboard()
        if st.session_state.current_test is None:
            st.sidebar.header("Previous Performance")
            show_comparative_analysis()

if __name__ == "__main__":
    main()

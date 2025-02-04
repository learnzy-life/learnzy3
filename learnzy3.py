# app.py
import streamlit as st
import firebase_admin
import time
import pandas as pd
from firebase_admin import credentials, auth, firestore
from streamlit.components.v1 import html
import json

# Firebase Configuration
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Firebase Web Configuration (Replace with your config)
firebase_config = {
  apiKey: "AIzaSyCLc4MGAeqehNLIGmLOtK3TA6fX1ftfkfA",
  authDomain: "learnzy3.firebaseapp.com",
  projectId: "learnzy3",
  storageBucket: "learnzy3.firebasestorage.app",
  messagingSenderId: "782772780808",
  appId: "1:782772780808:web:d458e2fc0bb5468fc1b6bd",
  measurementId: "G-Q5E06GFKNC"

}

# Initialize Session State
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_test' not in st.session_state:
    st.session_state.current_test = None
if 'test_started' not in st.session_state:
    st.session_state.test_started = False
if 'test_data' not in st.session_state:
    st.session_state.test_data = []
if 'start_time' not in st.session_state:
    st.session_state.start_time = None

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

# User Authentication Flow
def authenticate_user():
    st.title("Welcome to Learnzy! 📚")
    
    if not st.session_state.user:
        firebase_login()
        
        # Handle auth callback
        if 'token' in st.experimental_get_query_params():
            token = st.experimental_get_query_params()['token'][0]
            try:
                decoded_token = auth.verify_id_token(token)
                st.session_state.user = {
                    'uid': decoded_token['uid'],
                    'name': decoded_token['name'],
                    'email': decoded_token['email']
                }
                st.rerun()
            except Exception as e:
                st.error(f"Authentication failed: {str(e)}")

# Mock Test Dashboard
def show_dashboard():
    st.header(f"Welcome, {st.session_state.user['name']}!")
    st.subheader("Available Mock Tests")
    
    # Display 5 test cards
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.image("https://via.placeholder.com/150", width=100)
            if st.button(f"Test {i+1}", key=f"test_{i}"):
                st.session_state.current_test = i+1
                st.rerun()

# Test Syllabus Preview
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
        initialize_test()

# Initialize New Test
def initialize_test():
    st.session_state.test_started = True
    st.session_state.start_time = time.time()
    st.session_state.test_data = {
        'questions_attempted': 0,
        'correct_answers': 0,
        'score': 0,
        'responses': [],
        'time_remaining': 1800  # 30 minutes in seconds
    }
    st.rerun()

# Question Display and Answer Handling
def display_question(question):
    st.subheader(f"Question {question['id']}")
    st.write(question['text'])
    
    options = [question['A'], question['B'], question['C'], question['D']]
    selected = st.radio("Select your answer:", options, key=f"q_{question['id']}")
    
    if st.button("Next Question"):
        process_answer(question, selected)

def process_answer(question, selected):
    # Calculate time taken
    time_taken = time.time() - st.session_state.start_time
    st.session_state.start_time = time.time()
    
    # Update test data
    is_correct = (selected == question[question['answer']])
    
    st.session_state.test_data['questions_attempted'] += 1
    st.session_state.test_data['score'] += 4 if is_correct else -1
    st.session_state.test_data['correct_answers'] += 1 if is_correct else 0
    
    st.session_state.test_data['responses'].append({
        'question_id': question['id'],
        'topic': question['topic'],
        'subtopic': question['subtopic'],
        'correct': is_correct,
        'time_spent': time_taken
    })
    
    # Save progress to Firestore
    save_test_progress()

# Save Test Progress to Firestore
def save_test_progress():
    user_ref = db.collection('users').document(st.session_state.user['uid'])
    test_ref = user_ref.collection('mock_tests').document(f"test_{st.session_state.current_test}")
    
    test_ref.set({
        'start_time': firestore.SERVER_TIMESTAMP,
        'progress': st.session_state.test_data,
        'completed': False
    }, merge=True)

# Final Test Submission
def complete_test():
    # Calculate final metrics
    total_time = time.time() - st.session_state.start_time
    accuracy = (st.session_state.test_data['correct_answers'] / 30) * 100
    
    # Save final results
    user_ref = db.collection('users').document(st.session_state.user['uid'])
    test_ref = user_ref.collection('mock_tests').document(f"test_{st.session_state.current_test}")
    
    test_ref.set({
        'completed': True,
        'score': st.session_state.test_data['score'],
        'accuracy': accuracy,
        'time_taken': total_time,
        'timestamp': firestore.SERVER_TIMESTAMP,
        'responses': st.session_state.test_data['responses']
    }, merge=True)
    
    st.session_state.test_started = False
    st.rerun()

# Comparative Analysis
def show_comparative_analysis():
    st.header("📈 Performance Trends")
    
    # Get previous test data
    user_ref = db.collection('users').document(st.session_state.user['uid'])
    tests = user_ref.collection('mock_tests').stream()
    
    test_history = []
    for test in tests:
        data = test.to_dict()
        if data.get('completed'):
            test_history.append(data)
    
    if len(test_history) > 1:
        st.subheader("Accuracy Over Time")
        accuracy_data = pd.DataFrame({
            'Test': [f"Test {i+1}" for i in range(len(test_history))],
            'Accuracy': [t['accuracy'] for t in test_history]
        })
        st.line_chart(accuracy_data.set_index('Test'))
        
        st.subheader("Topic-wise Improvement")
        # Add topic comparison logic here
        
    else:
        st.info("Complete more tests to unlock comparative analysis!")

# Main App Flow
def main():
    if not st.session_state.user:
        authenticate_user()
    else:
        if st.session_state.test_started:
            # Test Interface
            st.header(f"Test {st.session_state.current_test} - In Progress")
            
            # Timer
            time_elapsed = time.time() - st.session_state.start_time
            time_remaining = max(1800 - time_elapsed, 0)
            mins, secs = divmod(time_remaining, 60)
            st.write(f"Time Remaining: {int(mins):02d}:{int(secs):02d}")
            
            # Question Display (Implement your question loading logic)
            # display_question(current_question)
            
            # Temporary test complete button
            if st.button("Complete Test"):
                complete_test()
        
        elif st.session_state.current_test:
            show_syllabus()
        else:
            show_dashboard()
            if st.session_state.current_test is None:
                st.sidebar.header("Previous Performance")
                show_comparative_analysis()

if __name__ == "__main__":
    main()

# app.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase
import pandas as pd
import time

# ---------------------------
# Firebase Configuration
# ---------------------------

# Initialize Firebase Admin
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Firebase Web Config (Replace with your config)
firebase_config = {
    "apiKey": "AIzaSyABCDEfghIJKLmnopQRSTUVwxyz1234567",
    "authDomain": "learnzy3.firebaseapp.com",
    "projectId": "learnzy3",
    "storageBucket": "learnzy3.appspot.com",
    "messagingSenderId": "123456789012",
    "appId": "1:123456789012:web:abcd1234efgh5678ijkl90"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# ---------------------------
# Authentication
# ---------------------------

def handle_login():
    try:
        user = auth.sign_in_with_email_and_password(st.session_state.email, st.session_state.password)
        st.session_state.user = user
        st.session_state.authenticated = True
        st.success("Login successful!")
        load_user_data(user['localId'])
    except Exception as e:
        st.error(f"Login failed: {str(e)}")

def load_user_data(user_id):
    user_ref = db.collection("users").document(user_id)
    doc = user_ref.get()
    if doc.exists:
        st.session_state.user_data = doc.to_dict()
    else:
        # Create new user document
        st.session_state.user_data = {
            "user_id": user_id,
            "email": st.session_state.email,
            "attempts": [],
            "created_at": firestore.SERVER_TIMESTAMP
        }
        user_ref.set(st.session_state.user_data)

# ---------------------------
# Test Management
# ---------------------------

def load_test(test_id):
    test_ref = db.collection("tests").document(str(test_id))
    test_data = test_ref.get().to_dict()
    return test_data.get("questions", [])

def save_attempt():
    attempt_data = {
        "test_id": st.session_state.current_test,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "score": st.session_state.score,
        "time_spent": time.time() - st.session_state.start_time,
        "details": st.session_state.user_answers
    }
    
    user_ref = db.collection("users").document(st.session_state.user['localId'])
    user_ref.update({
        "attempts": firestore.ArrayUnion([attempt_data])
    })

# ---------------------------
# Test Interface
# ---------------------------

def test_interface():
    st.header(f"Test {st.session_state.current_test}")
    
    # Timer
    elapsed = time.time() - st.session_state.start_time
    remaining = 1800 - int(elapsed)
    st.progress(remaining/1800)
    st.write(f"Time Left: {remaining//60:02d}:{remaining%60:02d}")
    
    # Question Display
    q = st.session_state.questions[st.session_state.current_question]
    
    st.subheader(f"Question {st.session_state.current_question + 1}")
    st.markdown(q['Question Text'])
    
    options = [q['Option A'], q['Option B'], q['Option C'], q['Option D']]
    answer = st.radio("Select Answer:", options, key=f"q{st.session_state.current_question}")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Next ➡️"):
            process_answer(q, answer)
            st.session_state.current_question += 1
            st.experimental_rerun()

def process_answer(q, answer):
    options = [q['Option A'], q['Option B'], q['Option C'], q['Option D']]
    selected_index = options.index(answer)
    
    st.session_state.user_answers[q['Question ID']] = {
        "selected": chr(65 + selected_index),
        "correct": q['Correct Answer'],
        "time_taken": time.time() - st.session_state.last_question_time
    }
    
    if st.session_state.user_answers[q['Question ID']]["selected"] == q['Correct Answer']:
        st.session_state.score += 4
    else:
        st.session_state.score -= 1
    
    st.session_state.last_question_time = time.time()

# ---------------------------
# Main App
# ---------------------------

def main():
    st.title("Learnzy Mock Test Platform")
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        with st.form("auth_form"):
            st.subheader("Login")
            st.text_input("Email", key="email")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Login", on_click=handle_login)
            
        if st.button("Sign in with Google"):
            st.write("Google login coming soon!")
    else:
        if 'current_test' not in st.session_state:
            # Dashboard
            st.header(f"Welcome {st.session_state.user_data['email']}!")
            
            cols = st.columns(3)
            for i in range(3):
                with cols[i]:
                    st.subheader(f"Test {i+1}")
                    st.write("30 Questions")
                    st.write("30 Minutes")
                    if st.button(f"Start Test {i+1}"):
                        st.session_state.current_test = i+1
                        st.session_state.questions = load_test(i+1)
                        st.session_state.start_time = time.time()
                        st.session_state.last_question_time = time.time()
                        st.session_state.current_question = 0
                        st.session_state.user_answers = {}
                        st.session_state.score = 0
                        st.experimental_rerun()
        else:
            if st.session_state.current_question < len(st.session_state.questions):
                test_interface()
            else:
                save_attempt()
                st.balloons()
                st.header("Test Completed!")
                st.metric("Final Score", st.session_state.score)
                st.write("Detailed analysis coming soon!")
                if st.button("Return to Dashboard"):
                    del st.session_state.current_test
                    st.experimental_rerun()

if __name__ == "__main__":
    main()

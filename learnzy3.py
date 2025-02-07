import streamlit as st
import pandas as pd
import time
from datetime import datetime

# ================== Configuration ==================
MOCKS = {
    'Mock Test 1': {'gid': '848132391'},
    'Mock Test 2': {'gid': '610172732'},
    'Mock Test 3': {'gid': '1133755197'},
    'Mock Test 4': {'gid': '690484996'},
    'Mock Test 5': {'gid': '160639837'}
}

BASE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvDpDbBzkcr1-yuTXAfYHvV6I0IzWHnU7SFF1ogGBK-PBIru25TthrwVJe3WiqTYchBoCiSyT0V1PJ/pub?output=csv&gid="

# ================== Session State ==================
def initialize_session_state():
    required_states = {
        'test_selected': None,
        'test_started': False,
        'current_question': 0,
        'user_answers': {},
        'question_start_time': time.time(),
        'show_syllabus': False
    }
    for key, value in required_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ================== Data Loading ==================
@st.cache_data(show_spinner="📖 Loading questions...")
def load_mock_data(gid):
    try:
        url = f"{BASE_SHEET_URL}{gid}"
        df = pd.read_csv(url)
        return df.to_dict(orient='records')
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return []

# ================== Welcome Page ==================
def show_welcome():
    st.title("🚀 ExamPrep Pro")
    st.markdown("""
    <style>
    .welcome-header {
        color: #2E86C1;
        text-align: center;
        font-size: 2.5em;
    }
    .mock-card {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .mock-card:hover {
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="welcome-header">Welcome to Smart Mock Test Platform!</div>', unsafe_allow_html=True)
    
    cols = st.columns(3)
    with cols[1]:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=150)

    st.subheader("📋 Available Mock Tests")
    for mock_name, mock_data in MOCKS.items():
        with st.container():
            st.markdown(f"""
            <div class="mock-card">
                <h3>{mock_name}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Add unique key for each button
            if st.button(f"Select {mock_name}", key=f"btn_{mock_name}"):
                st.session_state.test_selected = mock_data['gid']
                st.session_state.show_syllabus = True
                st.rerun()

# ================== Syllabus Popup ==================
def show_syllabus():
    if st.session_state.show_syllabus and st.session_state.test_selected:
        with st.expander("📚 Mock Test Syllabus", expanded=True):
            st.write("This test covers:")
            data = load_mock_data(st.session_state.test_selected)
            
            if not data:
                st.error("No questions loaded!")
                return
            
            subjects = list(set(q['Subject'] for q in data))
            topics = list(set(q['Topic'] for q in data))
            
            st.markdown(f"""
            - **Subjects Covered:** {', '.join(subjects)}
            - **Main Topics:** {', '.join(topics[:5])}
            - **Total Questions:** {len(data)}
            - **Suggested Time:** {sum(int(q['Time to Solve (seconds)']) for q in data)//60} minutes
            """)
            
            if st.button("🚀 Start Test Now", key="start_test"):
                st.session_state.test_started = True
                st.session_state.show_syllabus = False
                st.rerun()

# ================== Main Flow ==================
def main():
    if not st.session_state.test_selected:
        show_welcome()
    elif st.session_state.test_selected and not st.session_state.test_started:
        show_syllabus()
    elif st.session_state.test_started:
        data = load_mock_data(st.session_state.test_selected)
        if st.session_state.current_question < len(data):
            q = data[st.session_state.current_question]
            display_question(q)
        else:
            analyze_performance(data)

if __name__ == "__main__":
    main()

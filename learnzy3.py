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
        'authenticated': False,
        'test_selected': None,
        'test_started': False,
        'current_question': 0,
        'user_answers': {},
        'question_start_time': time.time(),
        'username': None,
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

# ================== New Components ==================
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
                <p>Contains {len(load_mock_data(mock_data['gid']))} questions</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select {mock_name}"):
                st.session_state.test_selected = mock_data['gid']
                st.session_state.show_syllabus = True
                st.rerun()

def show_syllabus():
    if st.session_state.show_syllabus:
        with st.expander("📚 Mock Test Syllabus", expanded=True):
            st.write("This test covers:")
            data = load_mock_data(st.session_state.test_selected)
            
            # Get unique subjects and topics
            subjects = list(set(q['Subject'] for q in data))
            topics = list(set(q['Topic'] for q in data))
            
            st.markdown(f"""
            - **Subjects Covered:** {', '.join(subjects)}
            - **Main Topics:** {', '.join(topics[:5])}
            - **Total Questions:** {len(data)}
            - **Suggested Time:** {sum(int(q['Time to Solve (seconds)']) for q in data)//60} minutes
            """)
            
            if st.button("🚀 Start Test Now"):
                st.session_state.test_started = True
                st.session_state.show_syllabus = False
                st.rerun()

# ================== Updated Question Display ==================
def display_question(q):
    st.subheader(f"Question {st.session_state.current_question + 1}")
    st.markdown(f"**Subject:** {q['Subject']} | **Topic:** {q['Topic']}")
    st.markdown(f"**Difficulty:** {q['Difficulty Level']} | **Time Benchmark:** {q['Time to Solve (seconds)']}s")
    
    st.markdown(f"### {q['Question Text']}")
    options = [q['Option A'], q['Option B'], q['Option C'], q['Option D']]
    answer = st.radio("Select your answer:", options, key=f"q{st.session_state.current_question}")
    
    # Time tracking
    time_spent = time.time() - st.session_state.question_start_time
    st.caption(f"Time spent: {int(time_spent)}s (Benchmark: {q['Time to Solve (seconds)']}s)")
    
    if st.button("Next ➡️"):
        process_answer(q, answer, time_spent)
        st.session_state.current_question += 1
        st.session_state.question_start_time = time.time()
        st.rerun()

# ================== Enhanced Analysis ==================
def analyze_performance(data):
    st.title("📈 Advanced Performance Report")
    
    total_time = sum(ans['time_taken'] for ans in st.session_state.user_answers.values())
    benchmark_time = sum(int(q['Time to Solve (seconds)']) for q in data)
    correct = sum(1 for ans in st.session_state.user_answers.values() if ans['selected'] == ans['correct'])
    
    # Difficulty Analysis
    difficulty_stats = {}
    for q in data:
        level = q['Difficulty Level']
        ans = st.session_state.user_answers[q['Question Number']]
        if level not in difficulty_stats:
            difficulty_stats[level] = {'correct': 0, 'total': 0, 'time': 0}
        difficulty_stats[level]['total'] += 1
        difficulty_stats[level]['correct'] += 1 if ans['selected'] == ans['correct'] else 0
        difficulty_stats[level]['time'] += ans['time_taken']
    
    # Time Analysis
    time_analysis = {
        'Your Time': total_time,
        'Benchmark Time': benchmark_time,
        'Time Difference': total_time - benchmark_time
    }
    
    # Subject-wise Analysis
    subject_stats = {}
    for q in data:
        subject = q['Subject']
        ans = st.session_state.user_answers[q['Question Number']]
        if subject not in subject_stats:
            subject_stats[subject] = {'correct': 0, 'total': 0}
        subject_stats[subject]['total'] += 1
        subject_stats[subject]['correct'] += 1 if ans['selected'] == ans['correct'] else 0
    
    # Display Analysis
    with st.expander("📊 Overall Summary", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Score", f"{correct}/{len(data)}")
        with col2:
            st.metric("Accuracy", f"{(correct/len(data))*100:.1f}%")
        with col3:
            st.metric("Time Efficiency", 
                     f"{total_time}s",
                     delta=f"{'Over' if time_analysis['Time Difference'] >0 else 'Under'} by {abs(time_analysis['Time Difference'])}s")
    
    with st.expander("📚 Subject-wise Breakdown"):
        for subject, stats in subject_stats.items():
            st.progress(stats['correct']/stats['total'], text=f"{subject} - {stats['correct']}/{stats['total']} ({stats['correct']/stats['total']*100:.1f}%)")
    
    with st.expander("⏱ Time Management Analysis"):
        st.bar_chart({
            'Your Time': [total_time],
            'Recommended Time': [benchmark_time]
        })
    
    if st.button("🔄 Take Another Test"):
        st.session_state.clear()
        st.rerun()

# ================== Main Flow ==================
def main():
    if not st.session_state.authenticated:
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

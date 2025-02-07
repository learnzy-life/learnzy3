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

REQUIRED_COLUMNS = [
    'Question Number', 'Question Text', 'Option A', 'Option B', 'Option C', 'Option D',
    'Correct Answer', 'Subject', 'Topic', 'Subtopic', 'Difficulty Level',
    'Question Structure', 'Bloom’s Taxonomy', 'Priority Level',
    'Time to Solve (seconds)', 'Key Concept Tested', 'Common Pitfalls'
]

BASE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvDpDbBzkcr1-yuTXAfYHvV6I0IzWHnU7SFF1ogGBK-PBIru25TthrwVJe3WiqTYchBoCiSyT0V1PJ/pub?output=csv&gid="

# ================== Session State ==================
def initialize_session_state():
    required_states = {
        'test_selected': None,
        'test_started': False,
        'current_question': 0,
        'user_answers': {},
        'question_start_time': time.time(),
        'show_syllabus': False,
        'data_loaded': False
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
        
        # Clean column names
        df.columns = df.columns.str.strip().str.title()
        
        # Validate columns
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            st.error(f"Missing columns in sheet: {', '.join(missing_cols)}")
            return None
            
        return df.to_dict(orient='records')
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return None

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
            
            if st.button(f"Select {mock_name}", key=f"btn_{mock_name}"):
                st.session_state.test_selected = mock_data['gid']
                st.session_state.show_syllabus = True
                st.session_state.data_loaded = False
                st.rerun()

# ================== Syllabus Popup ==================
def show_syllabus():
    if st.session_state.show_syllabus and st.session_state.test_selected:
        with st.expander("📚 Mock Test Syllabus", expanded=True):
            if not st.session_state.data_loaded:
                data = load_mock_data(st.session_state.test_selected)
                if data is None:
                    st.error("Failed to load test data")
                    return
                st.session_state.data_loaded = data
                
            data = st.session_state.data_loaded
            
            try:
                subjects = list(set(str(q.get('Subject', 'General')) for q in data))
                topics = list(set(str(q.get('Topic', 'General')) for q in data))
                
                st.markdown(f"""
                - **Subjects Covered:** {', '.join(subjects)}
                - **Main Topics:** {', '.join(topics[:5])}
                - **Total Questions:** {len(data)}
                - **Suggested Time:** {sum(int(q.get('Time to Solve (seconds)', 0)) for q in data)//60} minutes
                """)
                
                if st.button("🚀 Start Test Now", key="start_test"):
                    st.session_state.test_started = True
                    st.session_state.show_syllabus = False
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error displaying syllabus: {str(e)}")
                st.write("Actual columns present:", list(data[0].keys()))

# ================== Question Display ==================
def display_question(q):
    st.subheader(f"Question {st.session_state.current_question + 1}")
    st.markdown(f"**Subject:** {q.get('Subject', 'N/A')} | **Topic:** {q.get('Topic', 'N/A')}")
    st.markdown(f"**Difficulty:** {q.get('Difficulty Level', 'N/A')} | **Time Benchmark:** {q.get('Time to Solve (seconds)', 'N/A')}s")
    
    st.markdown(f"### {q.get('Question Text', 'Question text missing')}")
    
    options = [q.get('Option A', ''), q.get('Option B', ''), 
               q.get('Option C', ''), q.get('Option D', '')]
    answer = st.radio("Select your answer:", options, key=f"q{st.session_state.current_question}")
    
    time_spent = time.time() - st.session_state.question_start_time
    st.caption(f"Time spent: {int(time_spent)}s (Benchmark: {q.get('Time to Solve (seconds)', 'N/A')}s)")
    
    if st.button("Next ➡️"):
        process_answer(q, answer, time_spent)
        st.session_state.current_question += 1
        st.session_state.question_start_time = time.time()
        st.rerun()

# ================== Answer Processing ==================
def process_answer(q, answer, time_spent):
    question_id = q.get('Question Number', st.session_state.current_question)
    options = [q.get('Option A', ''), q.get('Option B', ''), 
               q.get('Option C', ''), q.get('Option D', '')]
    
    try:
        selected_option = chr(65 + options.index(answer))
    except ValueError:
        selected_option = 'X'
        
    st.session_state.user_answers[question_id] = {
        'selected': selected_option,
        'correct': q.get('Correct Answer', 'X'),
        'time_taken': time_spent
    }

# ================== Enhanced Analysis ==================
def analyze_performance(data):
    st.title("📈 Advanced Performance Report")
    
    try:
        total_time = sum(ans['time_taken'] for ans in st.session_state.user_answers.values())
        benchmark_time = sum(int(q.get('Time to Solve (seconds)', 0)) for q in data)
        correct = sum(1 for ans in st.session_state.user_answers.values() 
                     if ans['selected'] == ans['correct'])
        
        # Difficulty Analysis
        difficulty_stats = {}
        for q in data:
            level = q.get('Difficulty Level', 'Unknown')
            ans = st.session_state.user_answers.get(q['Question Number'], {})
            
            if level not in difficulty_stats:
                difficulty_stats[level] = {'correct': 0, 'total': 0, 'time': 0}
            
            difficulty_stats[level]['total'] += 1
            if ans.get('selected') == ans.get('correct'):
                difficulty_stats[level]['correct'] += 1
            difficulty_stats[level]['time'] += ans.get('time_taken', 0)
        
        # Display Analysis
        with st.expander("📊 Overall Summary", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Score", f"{correct}/{len(data)}")
            with col2:
                st.metric("Accuracy", f"{(correct/len(data))*100:.1f}%")
            with col3:
                delta = total_time - benchmark_time
                st.metric("Time Efficiency", f"{total_time:.0f}s",
                         delta=f"{'Over' if delta >0 else 'Under'} by {abs(delta):.0f}s")
        
        if st.button("🔄 Take Another Test"):
            st.session_state.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")

# ================== Main Flow ==================
def main():
    try:
        if not st.session_state.test_selected:
            show_welcome()
        elif st.session_state.test_selected and not st.session_state.test_started:
            show_syllabus()
        elif st.session_state.test_started:
            data = st.session_state.data_loaded
            if not data:
                st.error("No test data loaded!")
                return
                
            if st.session_state.current_question < len(data):
                q = data[st.session_state.current_question]
                display_question(q)
            else:
                analyze_performance(data)
                
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.write("Please refresh the page to restart")

if __name__ == "__main__":
    main()

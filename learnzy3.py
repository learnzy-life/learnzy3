import streamlit as st
import pandas as pd
import time

# ---------------------------
# CONFIGURATION & CONSTANTS
# ---------------------------

# Total test duration in seconds (40 minutes)
TEST_DURATION = 2400

# Google Sheets base CSV URL using the Sheet ID from your subsheet URLs
BASE_SHEET_ID = "1qrdURj3XHZHStT2BG1ndmq0LyFHGbvVVQSruBlkH9mk"
BASE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{BASE_SHEET_ID}/export?format=csv&gid="

# Mock test configuration: each test’s GID and a placeholder syllabus.
mock_tests = {
    "Mock Test 1": {
        "gid": "848132391",
        "syllabus": """**Syllabus for Mock Test 1:**
- Topics: Algebra, Geometry  
- Difficulty: Medium  
- Key Concepts: Linear Equations, Triangles, Circles  
- Focus: Problem-solving and time management."""
    },
    "Mock Test 2": {
        "gid": "610172732",
        "syllabus": """**Syllabus for Mock Test 2:**
- Topics: Calculus, Trigonometry  
- Difficulty: Hard  
- Key Concepts: Derivatives, Integrals, Sine & Cosine  
- Focus: Analytical reasoning and conceptual clarity."""
    },
    "Mock Test 3": {
        "gid": "1133755197",
        "syllabus": """**Syllabus for Mock Test 3:**
- Topics: Physics  
- Difficulty: Medium  
- Key Concepts: Mechanics, Thermodynamics  
- Focus: Application-based questions and theory."""
    },
    "Mock Test 4": {
        "gid": "690484996",
        "syllabus": """**Syllabus for Mock Test 4:**
- Topics: Chemistry  
- Difficulty: Medium  
- Key Concepts: Organic Chemistry, Periodic Table  
- Focus: Reaction mechanisms and periodic trends."""
    },
    "Mock Test 5": {
        "gid": "160639837",
        "syllabus": """**Syllabus for Mock Test 5:**
- Topics: Combined Subjects  
- Difficulty: Varied  
- Key Concepts: Mixed Problems across subjects  
- Focus: Overall time management and multi-topic integration."""
    }
}

# ---------------------------
# SESSION STATE INITIALIZATION
# ---------------------------
def initialize_session_state():
    default = {
        'current_page': 'welcome',  # Pages: welcome, selection, popup, test, analysis
        'selected_test': None,
        'test_started': False,
        'test_start_time': None,
        'current_question': 0,
        'user_answers': {},         # {question_index: answer_text}
        'question_times': {},       # {question_index: total time spent (sec)}
        'current_question_start': None,
        'test_submitted': False,
        'questions': None           # List of dicts loaded from CSV
    }
    for key, value in default.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ---------------------------
# DATA LOADING FUNCTION
# ---------------------------
@st.cache_data(show_spinner=False)
def load_test_data(gid):
    url = BASE_CSV_URL + gid
    try:
        df = pd.read_csv(url)
        return df.to_dict(orient='records')
    except Exception as e:
        st.error(f"Failed to load test data: {str(e)}")
        return []

# ---------------------------
# PAGE FUNCTIONS
# ---------------------------

def welcome_page():
    st.title("Welcome to Smart Mock Test Platform")
    st.write("Get ready to hustle and ace your exams!")
    if st.button("Start Hustling"):
        st.session_state.current_page = 'selection'
        st.rerun()

def selection_page():
    st.title("Select a Mock Test")
    st.write("Choose from the following tests:")
    for test_name in mock_tests.keys():
        # Display each test as a card-like button
        if st.button(test_name, key=test_name):
            st.session_state.selected_test = test_name
            st.session_state.current_page = 'popup'
            st.rerun()

def popup_page():
    test_name = st.session_state.selected_test
    config = mock_tests[test_name]
    st.markdown(f"## {test_name} - Syllabus")
    st.write(config["syllabus"])
    if st.button("Start Test"):
        st.session_state.test_started = True
        st.session_state.test_start_time = time.time()
        st.session_state.current_question_start = time.time()
        st.session_state.questions = load_test_data(config["gid"])
        st.session_state.current_page = 'test'
        st.rerun()
    if st.button("Back to Selection"):
        st.session_state.current_page = 'selection'
        st.rerun()

def test_page():
    # Timer & automatic submission check
    elapsed = time.time() - st.session_state.test_start_time
    remaining = max(0, TEST_DURATION - elapsed)
    minutes = int(remaining // 60)
    seconds = int(remaining % 60)
    st.sidebar.markdown(f"**Time Remaining:** {minutes:02d}:{seconds:02d}")
    if remaining <= 0:
        st.warning("Time's up! Submitting test...")
        st.session_state.test_submitted = True
        st.session_state.current_page = 'analysis'
        st.rerun()

    questions = st.session_state.questions
    if not questions:
        st.error("No questions loaded. Please check the data source.")
        return
    current_index = st.session_state.current_question
    q = questions[current_index]
    
    st.markdown(f"### Question {current_index + 1} of {len(questions)}")
    st.write(q["Question Text"])
    options = [q["Option A"], q["Option B"], q["Option C"], q["Option D"]]
    
    # Preserve previously selected answer (if any)
    prev_answer = st.session_state.user_answers.get(current_index, None)
    if prev_answer is None:
        default_index = 0
    else:
        try:
            default_index = options.index(prev_answer)
        except ValueError:
            default_index = 0
    answer = st.radio("Select your answer:", options, index=default_index, key=f"q{current_index}")
    st.session_state.user_answers[current_index] = answer

    # Navigation Buttons
    col1, col2, col3 = st.columns(3)
    # On navigation, record time spent on the current question.
    now = time.time()
    if col1.button("Previous") and current_index > 0:
        time_spent = now - st.session_state.current_question_start
        st.session_state.question_times[current_index] = st.session_state.question_times.get(current_index, 0) + time_spent
        st.session_state.current_question -= 1
        st.session_state.current_question_start = now
        st.rerun()
    if col2.button("Next") and current_index < len(questions) - 1:
        time_spent = now - st.session_state.current_question_start
        st.session_state.question_times[current_index] = st.session_state.question_times.get(current_index, 0) + time_spent
        st.session_state.current_question += 1
        st.session_state.current_question_start = now
        st.rerun()
    if col3.button("Submit Test"):
        time_spent = now - st.session_state.current_question_start
        st.session_state.question_times[current_index] = st.session_state.question_times.get(current_index, 0) + time_spent
        st.session_state.test_submitted = True
        st.session_state.current_page = 'analysis'
        st.rerun()

def analysis_page():
    st.balloons()
    st.title("Detailed Performance Report")
    questions = st.session_state.questions
    user_answers = st.session_state.user_answers
    question_times = st.session_state.question_times
    total_questions = len(questions)
    
    # Overall Metrics
    correct = 0
    total_user_time = 0
    total_ideal_time = 0
    for i, q in enumerate(questions):
        user_ans = user_answers.get(i, None)
        if user_ans is None:
            continue
        # Determine answer letter based on options ordering.
        opts = [q["Option A"], q["Option B"], q["Option C"], q["Option D"]]
        try:
            letter = chr(65 + opts.index(user_ans))
        except ValueError:
            letter = ""
        if letter == q["Correct Answer"]:
            correct += 1
        total_user_time += question_times.get(i, 0)
        try:
            total_ideal_time += float(q["Time to Solve (seconds)"])
        except:
            pass
    accuracy = (correct / total_questions) * 100 if total_questions > 0 else 0

    st.subheader("Overall Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Questions", total_questions)
    col2.metric("Correct Answers", correct)
    col3.metric("Accuracy", f"{accuracy:.1f}%")
    
    st.subheader("Time Analysis")
    col1, col2, col3 = st.columns(3)
    col1.metric("Your Total Time", f"{total_user_time:.1f} sec")
    col2.metric("Ideal Total Time", f"{total_ideal_time:.1f} sec")
    time_diff = total_user_time - total_ideal_time
    col3.metric("Time Difference", f"{abs(time_diff):.1f} sec", delta=f"{'Over' if time_diff > 0 else 'Under'} Ideal")
    
    # Topic-wise Analysis
    st.subheader("Topic-wise Breakdown")
    topic_stats = {}
    for i, q in enumerate(questions):
        topic = q["Topic"]
        if topic not in topic_stats:
            topic_stats[topic] = {"total": 0, "correct": 0, "user_time": 0, "ideal_time": 0}
        topic_stats[topic]["total"] += 1
        opts = [q["Option A"], q["Option B"], q["Option C"], q["Option D"]]
        user_ans = user_answers.get(i, None)
        try:
            letter = chr(65 + opts.index(user_ans)) if user_ans in opts else ""
        except:
            letter = ""
        if letter == q["Correct Answer"]:
            topic_stats[topic]["correct"] += 1
        topic_stats[topic]["user_time"] += question_times.get(i, 0)
        try:
            topic_stats[topic]["ideal_time"] += float(q["Time to Solve (seconds)"])
        except:
            pass

    topic_df = pd.DataFrame(topic_stats).T
    topic_df["accuracy"] = (topic_df["correct"] / topic_df["total"]) * 100
    topic_df["avg_user_time"] = topic_df["user_time"] / topic_df["total"]
    topic_df["avg_ideal_time"] = topic_df["ideal_time"] / topic_df["total"]
    topic_df["time_diff"] = topic_df["avg_user_time"] - topic_df["avg_ideal_time"]
    st.dataframe(topic_df)
    
    # Additional Insights based on other tags:
    st.subheader("Additional Insights")
    difficulty_counts = {}
    bloom_counts = {}
    priority_counts = {}
    for q in questions:
        diff = q.get("Difficulty Level", "Unknown")
        bloom = q.get("Bloom’s Taxonomy", "Unknown")
        priority = q.get("Priority Level", "Unknown")
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        bloom_counts[bloom] = bloom_counts.get(bloom, 0) + 1
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    st.write("**Difficulty Level Distribution:**", difficulty_counts)
    st.write("**Bloom’s Taxonomy Distribution:**", bloom_counts)
    st.write("**Priority Level Distribution:**", priority_counts)
    
    if st.button("Retake Test"):
        st.session_state.clear()
        st.rerun()

# ---------------------------
# MAIN APP FLOW
# ---------------------------
def main():
    page = st.session_state.current_page
    if page == 'welcome':
        welcome_page()
    elif page == 'selection':
        selection_page()
    elif page == 'popup':
        popup_page()
    elif page == 'test':
        test_page()
    elif page == 'analysis':
        analysis_page()
        
if __name__ == "__main__":
    main()

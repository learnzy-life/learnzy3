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

    # ---------------------------
    # Overall Metrics & Per Question Analysis
    # ---------------------------
    correct = 0
    total_user_time = 0
    total_ideal_time = 0
    per_question_data = []  # Holds data for each question for further time analysis

    for i, q in enumerate(questions):
        user_ans = user_answers.get(i, None)
        opts = [q["Option A"], q["Option B"], q["Option C"], q["Option D"]]
        letter = ""
        if user_ans in opts:
            try:
                letter = chr(65 + opts.index(user_ans))
            except Exception:
                letter = ""
        if letter == q["Correct Answer"]:
            correct += 1
        user_time = question_times.get(i, 0)
        total_user_time += user_time
        try:
            ideal_time = float(q["Time to Solve (seconds)"])
        except:
            ideal_time = 0
        total_ideal_time += ideal_time
        ratio = user_time / ideal_time if ideal_time > 0 else 0
        per_question_data.append({
            "Question": i + 1,
            "User Time": user_time,
            "Ideal Time": ideal_time,
            "Time Ratio": ratio
        })

    accuracy = (correct / total_questions) * 100 if total_questions > 0 else 0

    st.subheader("Overall Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Questions", total_questions)
    col2.metric("Correct Answers", correct)
    col3.metric("Accuracy", f"{accuracy:.1f}%")

    # ---------------------------
    # Time Management Analysis
    # ---------------------------
    st.subheader("Time Management Analysis")
    col1, col2, col3 = st.columns(3)
    col1.metric("Test Duration Allowed", f"{TEST_DURATION} sec")
    col2.metric("Your Total Time", f"{total_user_time:.1f} sec")
    col3.metric("Ideal Total Time", f"{total_ideal_time:.1f} sec")
    time_diff = total_user_time - total_ideal_time
    st.write(f"**Time Difference:** {'Over' if time_diff > 0 else 'Under'} Ideal by {abs(time_diff):.1f} sec")

    per_question_df = pd.DataFrame(per_question_data)
    st.write("**Per Question Time Analysis:**")
    st.dataframe(per_question_df)
    st.write("**Time Comparison Chart:**")
    st.bar_chart(per_question_df[["User Time", "Ideal Time"]])

    over_time_questions = per_question_df[per_question_df["Time Ratio"] > 1.5]
    quick_questions = per_question_df[(per_question_df["Time Ratio"] > 0) & (per_question_df["Time Ratio"] < 0.75)]
    
    st.write("**Questions Taking More Than 150% of Ideal Time:**")
    if not over_time_questions.empty:
        st.dataframe(over_time_questions)
    else:
        st.write("None")

    st.write("**Questions Solved Significantly Faster (Less than 75% of Ideal Time):**")
    if not quick_questions.empty:
        st.dataframe(quick_questions)
    else:
        st.write("None")

    # ---------------------------
    # Performance Breakdown by Subject/Topic
    # ---------------------------
    st.subheader("Performance Breakdown by Subject/Topic")
    subject_stats = {}
    for i, q in enumerate(questions):
        # Use 'Subject' if available, otherwise 'Topic', else default to "General"
        subject = q.get("Subject", q.get("Topic", "General"))
        if subject not in subject_stats:
            subject_stats[subject] = {"total": 0, "correct": 0, "user_time": 0, "ideal_time": 0}
        subject_stats[subject]["total"] += 1
        opts = [q["Option A"], q["Option B"], q["Option C"], q["Option D"]]
        user_ans = user_answers.get(i, None)
        letter = ""
        if user_ans in opts:
            try:
                letter = chr(65 + opts.index(user_ans))
            except Exception:
                letter = ""
        if letter == q["Correct Answer"]:
            subject_stats[subject]["correct"] += 1
        subject_stats[subject]["user_time"] += question_times.get(i, 0)
        try:
            subject_stats[subject]["ideal_time"] += float(q["Time to Solve (seconds)"])
        except:
            pass

    subject_df = pd.DataFrame(subject_stats).T
    subject_df["accuracy"] = (subject_df["correct"] / subject_df["total"]) * 100
    subject_df["avg_user_time"] = subject_df["user_time"] / subject_df["total"]
    subject_df["avg_ideal_time"] = subject_df["ideal_time"] / subject_df["total"]
    subject_df["Time Ratio"] = subject_df["avg_user_time"] / subject_df["avg_ideal_time"]
    
    # Present plain language insights for each subject/topic
    for subject, row in subject_df.iterrows():
        st.write(f"**{subject}**:")
        st.write(f"- You answered **{row['correct']} out of {row['total']}** questions correctly ({row['accuracy']:.1f}%).")
        st.write(f"- Your average time per question: **{row['avg_user_time']:.1f} sec** (Ideal: **{row['avg_ideal_time']:.1f} sec**).")
        if row['accuracy'] < 70:
            st.write(f"  - *Action:* Review key concepts in {subject} to improve your accuracy.")
        if row['Time Ratio'] > 1.2:
            st.write(f"  - *Action:* Practice timed drills in {subject} to reduce your response time.")
        if row['accuracy'] >= 70 and row['Time Ratio'] <= 1.2:
            st.write(f"  - *Well done!* Your performance in {subject} is on track.")
        st.write("---")
    
    # ---------------------------
    # Deep Insights (Plain Language)
    # ---------------------------
    st.subheader("Deep Insights")
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
    
    st.write("**Difficulty Level Summary:**")
    for level, count in difficulty_counts.items():
        st.write(f"- {level}: {count} question(s)")
    st.write("If you struggled with 'Hard' questions, consider revisiting those topics for a stronger foundation.")

    st.write("**Cognitive Level (Bloom's Taxonomy) Summary:**")
    for level, count in bloom_counts.items():
        st.write(f"- {level}: {count} question(s)")
    st.write("If questions that require higher-order thinking (such as Analysis or Synthesis) were challenging, try practicing those skills further.")

    st.write("**Priority Level Summary:**")
    for level, count in priority_counts.items():
        st.write(f"- {level}: {count} question(s)")
    st.write("Focus on high-priority topics to ensure a solid overall understanding.")

    # ---------------------------
    # Improvement Plan (Max 5 Items)
    # ---------------------------
    st.subheader("Improvement Plan")
    improvement_items = []
    
    # Recommendation from time management analysis
    if total_user_time > total_ideal_time:
        improvement_items.append(f"Improve time management by practicing timed drills (Over by {abs(time_diff):.1f} sec).")
    
    # Recommendations from subject/topic breakdown
    for subject, row in subject_df.iterrows():
        if row["accuracy"] < 70:
            improvement_items.append(f"Review key concepts in {subject} (Accuracy: {row['accuracy']:.1f}%).")
        if row["Time Ratio"] > 1.2:
            improvement_items.append(f"Practice timed exercises in {subject} (Time Ratio: {row['Time Ratio']:.2f}).")
    
    # Recommendations from deep insights
    if difficulty_counts.get("Hard", 0) > 0:
        improvement_items.append("Focus on challenging 'Hard' questions to boost your conceptual understanding.")
    if bloom_counts.get("Analysis", 0) > 0 or bloom_counts.get("Synthesis", 0) > 0:
        improvement_items.append("Enhance your higher-order thinking skills through targeted practice on analysis and synthesis questions.")
    
    # Remove duplicate recommendations and select only the first 5
    unique_improvements = list(dict.fromkeys(improvement_items))
    top_improvements = unique_improvements[:5]
    
    st.write("Based on your performance, here are the top areas to work on:")
    for idx, item in enumerate(top_improvements, 1):
        st.write(f"{idx}. {item}")

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

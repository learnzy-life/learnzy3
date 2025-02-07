import streamlit as st
import pandas as pd
import time

# ------------------------------------------------------------------
# 1. MOCK TESTS CONFIGURATION
# ------------------------------------------------------------------
# Define a dictionary for the five mock tests. Each item contains the
# export-to-CSV URL (note the conversion from your provided editing URL)
# and a placeholder syllabus description.
mock_tests = {
    "Mock Test 1": {
        "csv_url": "https://docs.google.com/spreadsheets/d/1qrdURj3XHZHStT2BG1ndmq0LyFHGbvVVQSruBlkH9mk/export?format=csv&gid=848132391",
        "syllabus": "Syllabus details for Mock Test 1:\n- Topic coverage: Algebra, Geometry\n- Key concepts: Linear Equations, Quadrilaterals\n- Practice Questions: 50"
    },
    "Mock Test 2": {
        "csv_url": "https://docs.google.com/spreadsheets/d/1qrdURj3XHZHStT2BG1ndmq0LyFHGbvVVQSruBlkH9mk/export?format=csv&gid=610172732",
        "syllabus": "Syllabus details for Mock Test 2:\n- Topic coverage: Calculus, Trigonometry\n- Key concepts: Derivatives, Sine & Cosine\n- Practice Questions: 45"
    },
    "Mock Test 3": {
        "csv_url": "https://docs.google.com/spreadsheets/d/1qrdURj3XHZHStT2BG1ndmq0LyFHGbvVVQSruBlkH9mk/export?format=csv&gid=1133755197",
        "syllabus": "Syllabus details for Mock Test 3:\n- Topic coverage: Physics fundamentals\n- Key concepts: Mechanics, Thermodynamics\n- Practice Questions: 40"
    },
    "Mock Test 4": {
        "csv_url": "https://docs.google.com/spreadsheets/d/1qrdURj3XHZHStT2BG1ndmq0LyFHGbvVVQSruBlkH9mk/export?format=csv&gid=690484996",
        "syllabus": "Syllabus details for Mock Test 4:\n- Topic coverage: Chemistry basics\n- Key concepts: Organic Reactions, Periodic Table\n- Practice Questions: 35"
    },
    "Mock Test 5": {
        "csv_url": "https://docs.google.com/spreadsheets/d/1qrdURj3XHZHStT2BG1ndmq0LyFHGbvVVQSruBlkH9mk/export?format=csv&gid=160639837",
        "syllabus": "Syllabus details for Mock Test 5:\n- Topic coverage: Combined subjects\n- Key concepts: Mixed problems\n- Practice Questions: 55"
    }
}

# ------------------------------------------------------------------
# 2. SESSION STATE INITIALIZATION
# ------------------------------------------------------------------
def initialize_session_state():
    if "selected_test" not in st.session_state:
        st.session_state.selected_test = None
    if "test_started" not in st.session_state:
        st.session_state.test_started = False
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "question_start_time" not in st.session_state:
        st.session_state.question_start_time = time.time()

initialize_session_state()

# ------------------------------------------------------------------
# 3. DATA LOADING FUNCTION
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data(csv_url):
    try:
        data = pd.read_csv(csv_url)
        return data.to_dict(orient='records')
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return []

# ------------------------------------------------------------------
# 4. HELPER FUNCTIONS
# ------------------------------------------------------------------
def get_video_suggestions(topic):
    video_suggestions = {
        'Math': 'https://www.youtube.com/watch?v=Q5H9P9_cLo4',
        'Physics': 'https://www.youtube.com/watch?v=7jB5guIhwcY',
        'Chemistry': 'https://www.youtube.com/watch?v=8glvj2zzVg4'
    }
    return video_suggestions.get(topic, "#")

# ------------------------------------------------------------------
# 5. TEST FLOW FUNCTIONS
# ------------------------------------------------------------------
def display_question(q, total_questions):
    st.subheader(f"Question {st.session_state.current_question + 1} of {total_questions}")
    st.markdown(f"**{q['Question Text']}**")
    
    options = [q['Option A'], q['Option B'], q['Option C'], q['Option D']]
    answer = st.radio("Select your answer:", 
                      options=options,
                      key=f"q{st.session_state.current_question}")
    
    if st.button("Next Question ➡️"):
        process_answer(q, answer)
        st.session_state.current_question += 1
        st.session_state.question_start_time = time.time()
        st.experimental_rerun()

def process_answer(q, answer):
    # Using "Question Number" as the key identifier in the new format
    question_id = q["Question Number"]
    options = [q['Option A'], q['Option B'], q['Option C'], q['Option D']]
    selected_option = chr(65 + options.index(answer))
    
    st.session_state.user_answers[question_id] = {
        'selected': selected_option,
        'correct': q['Correct Answer'],
        'time_taken': time.time() - st.session_state.question_start_time
    }

def show_results(questions):
    st.balloons()
    st.title("📊 Detailed Performance Report")
    
    total_time = sum(ans['time_taken'] for ans in st.session_state.user_answers.values())
    # Instead of calculating a “topper time,” we now sum the given benchmark times.
    benchmark_total_time = sum(float(q["Time to Solve (seconds)"]) for q in questions)
    correct = sum(1 for ans in st.session_state.user_answers.values() if ans['selected'] == ans['correct'])
    accuracy = (correct / len(questions)) * 100

    # --- Time Analysis Section ---
    st.header("⏱ Time Analysis")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Your Total Time", f"{total_time:.1f}s")
    with col2:
        st.metric("Benchmark Time", f"{benchmark_total_time:.1f}s")
    with col3:
        delta = total_time - benchmark_total_time
        st.metric("Time Difference", f"{abs(delta):.1f}s", 
                  delta=f"{'Over' if delta > 0 else 'Under'} Benchmark")
    
    # --- Topic-wise Analysis ---
    st.header("📚 Topic-wise Breakdown")
    topic_stats = {}
    for q in questions:
        topic = q["Topic"]
        ans = st.session_state.user_answers.get(q["Question Number"])
        if not ans:
            continue
        if topic not in topic_stats:
            topic_stats[topic] = {
                'total_questions': 0,
                'correct': 0,
                'total_user_time': 0,
                'total_benchmark_time': 0
            }
        topic_stats[topic]['total_questions'] += 1
        topic_stats[topic]['correct'] += 1 if ans['selected'] == ans['correct'] else 0
        topic_stats[topic]['total_user_time'] += ans['time_taken']
        topic_stats[topic]['total_benchmark_time'] += float(q["Time to Solve (seconds)"])
    
    analysis_df = pd.DataFrame.from_dict(topic_stats, orient='index')
    analysis_df['accuracy'] = (analysis_df['correct'] / analysis_df['total_questions']) * 100
    analysis_df['avg_user_time'] = analysis_df['total_user_time'] / analysis_df['total_questions']
    analysis_df['avg_benchmark_time'] = analysis_df['total_benchmark_time'] / analysis_df['total_questions']
    analysis_df['time_difference'] = analysis_df['avg_user_time'] - analysis_df['avg_benchmark_time']
    analysis_df['status'] = analysis_df['accuracy'].apply(lambda x: '🚨 Needs Improvement' if x < 70 else '✅ Strong')
    
    for topic, data in analysis_df.iterrows():
        with st.expander(f"{topic} Analysis", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Accuracy**")
                st.progress(data['accuracy']/100)
                st.caption(f"{data['correct']}/{data['total_questions']} Correct")
                st.metric("Accuracy Score", f"{data['accuracy']:.1f}%")
                
                if data['accuracy'] < 70:
                    st.markdown(f"📚 [Improvement Video]({get_video_suggestions(topic)})")
            
            with col2:
                st.markdown("**Time Comparison**")
                st.metric("Your Avg Time", f"{data['avg_user_time']:.1f}s")
                st.metric("Benchmark Avg Time", f"{data['avg_benchmark_time']:.1f}s")
                st.metric("Time Difference", 
                          f"{abs(data['time_difference']):.1f}s",
                          delta=f"{'Faster' if data['time_difference'] < 0 else 'Slower'}")
            
            with col3:
                st.markdown("**Recommendations**")
                if data['accuracy'] < 70:
                    st.error("Focus on this topic!")
                    st.write("Practice similar questions:")
                    st.write(f"- [Practice Set]({get_video_suggestions(topic)})")
                else:
                    st.success("You're doing great!")
                    st.write("Challenge yourself:")
                    st.write(f"- [Advanced Problems]({get_video_suggestions(topic)})")
    
    # --- Subject-wise Analysis ---
    st.header("📖 Subject-wise Breakdown")
    subject_stats = {}
    for q in questions:
        subject = q["Subject"]
        ans = st.session_state.user_answers.get(q["Question Number"])
        if not ans:
            continue
        if subject not in subject_stats:
            subject_stats[subject] = {
                'total_questions': 0,
                'correct': 0,
                'total_user_time': 0,
                'total_benchmark_time': 0
            }
        subject_stats[subject]['total_questions'] += 1
        subject_stats[subject]['correct'] += 1 if ans['selected'] == ans['correct'] else 0
        subject_stats[subject]['total_user_time'] += ans['time_taken']
        subject_stats[subject]['total_benchmark_time'] += float(q["Time to Solve (seconds)"])
    
    subject_df = pd.DataFrame.from_dict(subject_stats, orient='index')
    subject_df['accuracy'] = (subject_df['correct'] / subject_df['total_questions']) * 100
    subject_df['avg_user_time'] = subject_df['total_user_time'] / subject_df['total_questions']
    subject_df['avg_benchmark_time'] = subject_df['total_benchmark_time'] / subject_df['total_questions']
    subject_df['time_difference'] = subject_df['avg_user_time'] - subject_df['avg_benchmark_time']
    
    st.dataframe(subject_df[['accuracy', 'avg_user_time', 'avg_benchmark_time', 'time_difference']])
    
    # --- Additional Insights using new tags ---
    st.header("🎯 Additional Insights")
    # Difficulty Level Distribution
    difficulty_counts = {}
    for q in questions:
        level = q["Difficulty Level"]
        difficulty_counts[level] = difficulty_counts.get(level, 0) + 1
    st.subheader("Difficulty Level Distribution")
    st.write(difficulty_counts)
    
    # Priority Level Distribution
    priority_counts = {}
    for q in questions:
        level = q["Priority Level"]
        priority_counts[level] = priority_counts.get(level, 0) + 1
    st.subheader("Priority Level Distribution")
    st.write(priority_counts)
    
    # --- Final Summary ---
    st.header("🎯 Key Insights")
    weak_topics = analysis_df[analysis_df['accuracy'] < 70].index.tolist()
    if weak_topics:
        st.error(f"**Priority Areas:** {', '.join(weak_topics)}")
    else:
        st.success("**Excellent Performance!** Keep up the good work!")
    
    st.markdown(f"""
    - **Overall Accuracy:** {accuracy:.1f}%
    - **Total Test Duration:** {total_time:.1f}s
    - **Benchmark Total Time:** {benchmark_total_time:.1f}s
    - **Most Time-Consuming Topic:** {analysis_df['avg_user_time'].idxmax()} ({analysis_df['avg_user_time'].max():.1f}s avg)
    """)
    
    if st.button("🔄 Retake Test"):
        # Clear all session state so the user can restart from the welcome page
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.experimental_rerun()

# ------------------------------------------------------------------
# 6. MAIN APP FLOW
# ------------------------------------------------------------------
def main():
    st.title("📝 Smart Mock Test Platform")
    initialize_session_state()
    
    # 6a. If no test has been selected, show the welcome & selection page.
    if st.session_state.selected_test is None:
        st.header("Welcome to the Smart Mock Test Platform")
        st.write("Please select a mock test to begin:")
        for test_name in mock_tests.keys():
            if st.button(test_name, key=test_name):
                st.session_state.selected_test = test_name
                st.experimental_rerun()
        return  # Wait for the user to choose a test.
    
    # 6b. If a test has been selected but not started, show the syllabus modal.
    if not st.session_state.test_started:
        test_info = mock_tests[st.session_state.selected_test]
        with st.modal(f"{st.session_state.selected_test} - Syllabus"):
            st.write(test_info["syllabus"])
            if st.button("Start Test"):
                st.session_state.test_started = True
                st.experimental_rerun()
        return
    
    # 6c. Once the test has started, load the selected test’s questions.
    test_info = mock_tests[st.session_state.selected_test]
    questions = load_data(test_info["csv_url"])
    if not questions:
        st.error("Failed to load questions. Please check the data source.")
        return
    
    # 6d. Test Flow: Display each question one by one and, once done, show results.
    if st.session_state.current_question < len(questions):
        q = questions[st.session_state.current_question]
        display_question(q, len(questions))
    else:
        show_results(questions)

if __name__ == "__main__":
    main()

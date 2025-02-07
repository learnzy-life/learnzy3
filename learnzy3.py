import streamlit as st
import pandas as pd

# Mapping of mock tests with GID values
mock_tests = {
    "Mock Test 1": "848132391",
    "Mock Test 2": "610172732",
    "Mock Test 3": "1133755197",
    "Mock Test 4": "690484996",
    "Mock Test 5": "160639837"
}

# Base Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1qrdURj3XHZHStT2BG1ndmq0LyFHGbvVVQSruBlkH9mk/export?format=csv&gid="

# Function to fetch mock test data
def load_mock_test(gid):
    url = SHEET_URL + gid
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error("Error loading the mock test data. Please try again.")
        return None

# Function to display mock test selection
def mock_test_selection():
    st.title("Welcome to Learnzy Mock Tests 🎯")
    st.subheader("Select a Mock Test to Begin")

    selected_test = st.selectbox("Choose a Mock Test:", list(mock_tests.keys()))

    if st.button("View Details"):
        st.session_state["selected_test"] = selected_test
        st.session_state["mock_data"] = load_mock_test(mock_tests[selected_test])
        st.rerun()

# Function to start the mock test
def start_mock_test():
    if "selected_test" not in st.session_state or "mock_data" not in st.session_state:
        st.error("No mock test selected. Please go back and choose one.")
        if st.button("Go Back"):
            del st.session_state["selected_test"]
            del st.session_state["mock_data"]
            st.rerun()
        return

    st.title(f"{st.session_state['selected_test']} 📖")
    st.subheader("Answer the questions below:")

    mock_data = st.session_state["mock_data"]
    
    if mock_data is not None:
        total_questions = len(mock_data)
        user_answers = {}

        for i in range(total_questions):
            question = mock_data.iloc[i]
            st.markdown(f"**Q{i+1}: {question['Question Text']}**")
            
            options = [question["Option A"], question["Option B"], question["Option C"], question["Option D"]]
            user_answers[i] = st.radio(f"Select an answer for Q{i+1}:", options, key=f"q{i}")

        if st.button("Submit Test"):
            st.session_state["user_answers"] = user_answers
            st.session_state["mock_data"] = mock_data
            st.rerun()

# Function to analyze the results
def analyze_results():
    if "user_answers" not in st.session_state or "mock_data" not in st.session_state:
        st.error("No test data found. Please start a test first.")
        if st.button("Go Back to Home"):
            st.session_state.clear()
            st.rerun()
        return

    st.title("Mock Test Analysis 📊")

    mock_data = st.session_state["mock_data"]
    user_answers = st.session_state["user_answers"]

    correct_count = 0
    total_questions = len(mock_data)
    total_time = 0

    st.subheader("Results Breakdown:")

    for i in range(total_questions):
        question = mock_data.iloc[i]
        correct_answer = question["Correct Answer"]
        user_answer = user_answers[i]
        time_to_solve = question["Time to Solve (seconds)"]
        total_time += time_to_solve

        if user_answer == correct_answer:
            correct_count += 1
            st.success(f"✅ Q{i+1}: Correct! ({time_to_solve} sec)")
        else:
            st.error(f"❌ Q{i+1}: Incorrect. Correct Answer: {correct_answer} ({time_to_solve} sec)")

    accuracy = (correct_count / total_questions) * 100
    avg_time_per_question = total_time / total_questions if total_questions > 0 else 0

    st.subheader("Final Score:")
    st.write(f"**Total Questions:** {total_questions}")
    st.write(f"**Correct Answers:** {correct_count}")
    st.write(f"**Accuracy:** {accuracy:.2f}%")
    st.write(f"**Average Time Per Question:** {avg_time_per_question:.2f} seconds")

    if st.button("Retake Test"):
        del st.session_state["user_answers"]
        del st.session_state["mock_data"]
        st.rerun()

# Main function to control app flow
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", ["Home", "Start Mock Test", "Results Analysis"])

    if page == "Home":
        mock_test_selection()
    elif page == "Start Mock Test":
        start_mock_test()
    elif page == "Results Analysis":
        analyze_results()

if __name__ == "__main__":
    main()

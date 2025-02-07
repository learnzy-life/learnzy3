import streamlit as st
import pandas as pd
import time
import unicodedata

# ================== Configuration ==================
MOCKS = {
    'Mock Test 1': {'gid': '848132391'},
    'Mock Test 2': {'gid': '610172732'},
    'Mock Test 3': {'gid': '1133755197'},
    'Mock Test 4': {'gid': '690484996'},
    'Mock Test 5': {'gid': '160639837'}
}

EXPECTED_COLUMNS = {
    'question_number': ['questionno', 'qno', 'number'],
    'question_text': ['question', 'text'],
    'option_a': ['a', 'option1'],
    'option_b': ['b', 'option2'],
    'option_c': ['c', 'option3'],
    'option_d': ['d', 'option4'],
    'correct_answer': ['answer', 'correct'],
    'subject': ['sub', 'category'],
    'topic': ['chapter'],
    'subtopic': ['subchapter'],
    'difficulty_level': ['difficulty'],
    'question_structure': ['type'],
    'blooms_taxonomy': ['bloom', 'taxonomy'],
    'priority_level': ['priority'],
    'time_to_solve': ['time', 'duration'],
    'key_concept': ['concept'],
    'common_pitfalls': ['pitfalls']
}

BASE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvDpDbBzkcr1-yuTXAfYHvV6I0IzWHnU7SFF1ogGBK-PBIru25TthrwVJe3WiqTYchBoCiSyT0V1PJ/pub?output=csv&gid="

# ================== Text Normalization ==================
def normalize_text(text):
    """Normalize text for robust column name matching"""
    text = unicodedata.normalize('NFKD', str(text).strip().lower())
    return ''.join([c for c in text if not unicodedata.combining(c)]).replace(' ', '_')

# ================== Column Validation ==================
def validate_columns(df_columns):
    """Match actual columns to expected columns with fuzzy matching"""
    column_map = {}
    warnings = []
    
    normalized_expected = {
        normalize_text(k): (k, aliases) 
        for k, aliases in EXPECTED_COLUMNS.items()
    }
    
    for actual_col in df_columns:
        normalized_actual = normalize_text(actual_col)
        
        # Check direct matches first
        matched = False
        for exp_key, (formal_name, aliases) in normalized_expected.items():
            all_variants = [exp_key] + [normalize_text(a) for a in aliases]
            if normalized_actual in all_variants:
                column_map[actual_col] = formal_name
                matched = True
                break
        
        if not matched:
            warnings.append(f"Unrecognized column: '{actual_col}'")
            column_map[actual_col] = None  # Track unrecognized columns
    
    # Check for missing required columns
    missing_formal = [
        formal for formal in EXPECTED_COLUMNS.keys()
        if formal not in column_map.values()
    ]
    
    return column_map, warnings, missing_formal

# ================== Data Loading ==================
@st.cache_data(show_spinner=False)
def load_mock_data(gid):
    try:
        url = f"{BASE_SHEET_URL}{gid}"
        df = pd.read_csv(url)
        
        # Normalize and validate columns
        column_map, warnings, missing = validate_columns(df.columns)
        
        if missing:
            st.error(f"Missing critical columns: {', '.join(missing)}")
            st.error("Please check your sheet column names and try again")
            return None, warnings
        
        # Rename columns using formal names
        df = df.rename(columns=column_map).dropna(axis=1, how='all')
        df = df[[col for col in column_map.values() if col is not None]]
        
        # Convert time to numeric
        if 'time_to_solve' in df.columns:
            df['time_to_solve'] = pd.to_numeric(df['time_to_solve'], errors='coerce')
        
        return df.to_dict('records'), warnings
        
    except Exception as e:
        st.error(f"Data loading failed: {str(e)}")
        return None, [str(e)]

# ================== Enhanced Syllabus Display ==================
def show_syllabus():
    if st.session_state.show_syllabus and st.session_state.test_selected:
        with st.expander("📚 Mock Test Syllabus", expanded=True):
            if not st.session_state.data_loaded:
                data, warnings = load_mock_data(st.session_state.test_selected)
                if data is None:
                    st.error("Failed to load test data")
                    for warn in warnings:
                        st.warning(warn)
                    return
                st.session_state.data_loaded = data
                st.session_state.load_warnings = warnings
                
            data = st.session_state.data_loaded
            warnings = st.session_state.load_warnings
            
            # Show data warnings
            if warnings:
                st.warning("Data Loading Warnings:")
                for warn in warnings:
                    st.write(f"- {warn}")
            
            try:
                subjects = list({str(q.get('subject', 'General')) for q in data})
                topics = list({str(q.get('topic', 'General')) for q in data})
                
                st.markdown(f"""
                **Test Overview**
                - 📚 Subjects: {', '.join(subjects[:3])}{'...' if len(subjects) > 3 else ''}
                - 📖 Topics: {', '.join(topics[:5])}{'...' if len(topics) > 5 else ''}
                - ❓ Total Questions: {len(data)}
                - ⏳ Estimated Duration: {sum(q.get('time_to_solve', 0) for q in data)//60} minutes
                """)
                
                if st.button("🚀 Start Test Now", key="start_test"):
                    st.session_state.test_started = True
                    st.session_state.show_syllabus = False
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error displaying syllabus: {str(e)}")

# Rest of the code remains the same as previous version (display_question, process_answer, analyze_performance, etc.)
# ...

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

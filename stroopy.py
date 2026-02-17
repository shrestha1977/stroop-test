import streamlit as st
import random
import time
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# -------------------- CONFIG --------------------
TOTAL_QUESTIONS = 20
TIME_LIMIT = 15  # seconds

COLORS = {
    "RED": "red",
    "GREEN": "green",
    "BLUE": "blue",
    "YELLOW": "yellow"
}

# -------------------- FUNCTIONS --------------------
def generate_question():
    word = random.choice(list(COLORS.keys()))
    color = random.choice(list(COLORS.values()))
    return word, color

def record_response(results, q_no, word, color, answer, correct, rt):
    results.append({
        "Question": q_no,
        "Word": word,
        "Color": color,
        "Answer": answer if answer else "No Response",
        "Correct": correct,
        "Reaction Time (s)": rt if rt is not None else "-"
    })

def next_question():
    st.session_state.q_index += 1
    st.session_state.start_time = time.time()
    st.session_state.answered = False
    st.session_state.word, st.session_state.color = generate_question()

# -------------------- SESSION STATE --------------------
if "q_index" not in st.session_state:
    st.session_state.q_index = 1
    st.session_state.results = []
    st.session_state.start_time = time.time()
    st.session_state.word, st.session_state.color = generate_question()
    st.session_state.answered = False

# -------------------- APP --------------------
st.title("🧠 Stroop Test")

# -------------------- TEST FINISHED --------------------
if st.session_state.q_index > TOTAL_QUESTIONS:
    st.success("Test Completed!")

    df = pd.DataFrame(st.session_state.results)
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "Download Results as CSV",
        df.to_csv(index=False),
        "stroop_results.csv",
        "text/csv"
    )

    st.stop()

# -------------------- TIMER --------------------
elapsed = time.time() - st.session_state.start_time
remaining = max(0, int(TIME_LIMIT - elapsed))

st_autorefresh(interval=1000, key="timer")

st.write(f"### Question {st.session_state.q_index} of {TOTAL_QUESTIONS}")
st.warning(f"⏱ Time left: **{remaining} seconds**")

# -------------------- QUESTION --------------------
st.markdown(
    f"<h1 style='color:{st.session_state.color}; text-align:center;'>"
    f"{st.session_state.word}</h1>",
    unsafe_allow_html=True
)

# -------------------- ANSWER BUTTONS --------------------
cols = st.columns(4)
for i, col in enumerate(cols):
    color_name = list(COLORS.keys())[i]
    with col:
        if st.button(color_name, key=f"{st.session_state.q_index}_{color_name}") and not st.session_state.answered:
            rt = round(elapsed, 2)
            correct = color_name.lower() == st.session_state.color

            record_response(
                st.session_state.results,
                st.session_state.q_index,
                st.session_state.word,
                st.session_state.color,
                color_name,
                correct,
                rt
            )

            st.session_state.answered = True
            next_question()
            st.rerun()

# -------------------- TIMEOUT HANDLING --------------------
if remaining == 0 and not st.session_state.answered:
    record_response(
        st.session_state.results,
        st.session_state.q_index,
        st.session_state.word,
        st.session_state.color,
        None,
        False,
        None
    )

    next_question()
    st.rerun()

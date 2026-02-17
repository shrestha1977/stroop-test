# stroopy.py
"""
Stroopy — Color–Word Stroop Test
- No practice trials
- No cognitive decline logic
- 15-second timer per question with auto-advance
"""

import streamlit as st
import random
import time
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# ------------------ CONFIG ------------------
COLOR_NAMES = ["RED", "GREEN", "BLUE", "YELLOW"]
COLOR_HEX = {
    "RED": "#d62828",
    "GREEN": "#2a9d8f",
    "BLUE": "#0077b6",
    "YELLOW": "#f4d35e"
}

TRIALS_TOTAL = 20
MAX_RT = 15.0
MIN_VALID_RT = 0.10
ISI = 0.5
CONGRUENT_PROPORTION = 0.5
# --------------------------------------------


def make_trial(congruent: bool):
    word = random.choice(COLOR_NAMES)
    ink = word if congruent else random.choice([c for c in COLOR_NAMES if c != word])
    return {"word": word, "ink": ink, "congruent": congruent}


def make_block(n, cong_prop=0.5):
    n_cong = int(round(n * cong_prop))
    n_incong = n - n_cong
    trials = [make_trial(True) for _ in range(n_cong)] + \
             [make_trial(False) for _ in range(n_incong)]
    random.shuffle(trials)
    return trials


def show_stimulus(trial):
    st.markdown(
        f"""
        <div style='text-align:center; margin-top:40px;'>
            <span style='font-size:110px; font-weight:700;
                         color:{COLOR_HEX[trial['ink']]};'>
                {trial['word']}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


# ✅ SAFE RESPONSE HANDLING (FIXED)
def record_response(results, trial, response_key, rt):
    if response_key is None:
        correct = 0
    else:
        correct = int(response_key.upper() == trial["ink"][0])

    results.append({
        "trial_index": len(results) + 1,
        "word_text": trial["word"],
        "ink_color": trial["ink"],
        "congruent": trial["congruent"],
        "response_key": response_key,
        "correct": correct,
        "rt_s": rt
    })


# ---------------- Session State ----------------
if "stage" not in st.session_state:
    st.session_state.stage = "instructions"
if "trials" not in st.session_state:
    st.session_state.trials = make_block(TRIALS_TOTAL, CONGRUENT_PROPORTION)
if "idx" not in st.session_state:
    st.session_state.idx = 0
if "results" not in st.session_state:
    st.session_state.results = []
if "onset" not in st.session_state:
    st.session_state.onset = None

# ---------------- UI ----------------
st.set_page_config(page_title="Stroopy", layout="centered")
st.title("Stroopy — Color–Word Test")


# ---------------- Instructions ----------------
if st.session_state.stage == "instructions":
    st.markdown("""
    ### Instructions
    - Ignore the word text
    - Select the **ink color**
    - You have **15 seconds per question**
    - If time runs out, it moves on automatically
    """)

    if st.button("Start Test"):
        st.session_state.stage = "test"
        st.session_state.idx = 0
        st.session_state.results = []
        st.session_state.onset = None
        st.rerun()


# ---------------- Test ----------------
elif st.session_state.stage == "test":

    # 🔁 REQUIRED for timer
    st_autorefresh(interval=1000, key="stroop_timer")

    idx = st.session_state.idx
    total = len(st.session_state.trials)

    if idx >= total:
        st.session_state.stage = "finished"
        st.rerun()

    trial = st.session_state.trials[idx]
    st.write(f"### Trial {idx + 1} / {total}")
    show_stimulus(trial)

    if st.session_state.onset is None:
        st.session_state.onset = time.time()

    elapsed = time.time() - st.session_state.onset
    remaining = max(0, int(MAX_RT - elapsed))

    st.warning(f"⏳ Time left: {remaining} seconds")

    # ⏰ TIMEOUT → AUTO ADVANCE
    if elapsed >= MAX_RT:
        record_response(
            st.session_state.results,
            trial,
            response_key=None,
            rt=None
        )
        time.sleep(ISI)
        st.session_state.idx += 1
        st.session_state.onset = None
        st.rerun()

    cols = st.columns(4)
    for i, color in enumerate(COLOR_NAMES):
        if cols[i].button(color):
            rt = time.time() - st.session_state.onset
            rt = rt if rt >= MIN_VALID_RT else None
            record_response(
                st.session_state.results,
                trial,
                color[0],
                rt
            )
            time.sleep(ISI)
            st.session_state.idx += 1
            st.session_state.onset = None
            st.rerun()


# ---------------- Results ----------------
elif st.session_state.stage == "finished":
    st.header("Results")

    df = pd.DataFrame(st.session_state.results)

    if df.empty:
        st.info("No data collected.")
    else:
        df["rt_clean"] = df["rt_s"].where(
            df["rt_s"].notnull() & (df["rt_s"] >= MIN_VALID_RT)
        )

        st.metric("Overall Accuracy (%)", f"{df['correct'].mean() * 100:.1f}")
        st.metric("Mean Reaction Time (s)", f"{df['rt_clean'].mean():.3f}")

        cong = df[df["congruent"]]
        incong = df[~df["congruent"]]

        st.write("### Stroop Effect")
        st.write({
            "Congruent Mean RT (s)": cong["rt_clean"].mean(),
            "Incongruent Mean RT (s)": incong["rt_clean"].mean(),
            "Interference (s)": incong["rt_clean"].mean() - cong["rt_clean"].mean()
        })

        st.write("### Trial-Level Data")
        st.dataframe(df)

        st.download_button(
            "Download Results (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            "stroopy_results.csv",
            "text/csv"
        )

    if st.button("Restart Test"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# stroopy.py
"""
Stroopy — a standalone Stroop test (color-word) Streamlit app.
- Button-first implementation (works without extra packages).
- Optional keyboard integration snippet is included and commented (requires streamlit-js-eval).
"""
import streamlit as st
import random
import time
import pandas as pd
from io import StringIO

# ------------------ CONFIG ------------------
COLOR_NAMES = ["RED", "GREEN", "BLUE", "YELLOW"]
COLOR_HEX = {
    "RED": "#d62828",
    "GREEN": "#2a9d8f",
    "BLUE": "#0077b6",
    "YELLOW": "#f4d35e"
}
TRIALS_TOTAL = 20       # total experimental trials (recommend 60-120)
PRACTICE_TRIALS = 8
MAX_RT = 3.0            # seconds (timeout)
MIN_VALID_RT = 0.10     # seconds (ignore anticipatory <100ms)
ISI = 0.5               # inter-stimulus interval (seconds)
CONGRUENT_PROPORTION = 0.5
# --------------------------------------------

def make_trial(congruent: bool):
    word = random.choice(COLOR_NAMES)
    if congruent:
        ink = word
    else:
        ink = random.choice([c for c in COLOR_NAMES if c != word])
    return {"word": word, "ink": ink, "congruent": congruent}

def make_block(n, cong_prop=0.5):
    n_cong = int(round(n * cong_prop))
    n_incong = n - n_cong
    trials = [make_trial(True) for _ in range(n_cong)] + [make_trial(False) for _ in range(n_incong)]
    random.shuffle(trials)
    return trials

def show_stimulus(trial):
    st.markdown(
        f"<div style='text-align:center; margin-top:40px;'>"
        f"<span style='font-size:110px; font-weight:700; color:{COLOR_HEX[trial['ink']]};'>{trial['word']}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

def record_response(results, trial, response_key, rt, practice=False):
    correct = (response_key is not None and response_key.upper() == trial["ink"][0])
    rec = {
        "trial_index": len(results) + 1,
        "word_text": trial["word"],
        "ink_color": trial["ink"],
        "congruent": trial["congruent"],
        "response_key": response_key.upper() if response_key else None,
        "correct": int(correct) if response_key else 0,
        "rt_s": rt if response_key else None,
        "practice": practice,
        "timestamp_onset": st.session_state.current_onset if "current_onset" in st.session_state else None,
        "timestamp_response": time.time() if response_key else None
    }
    results.append(rec)

# ---------------- Session state init ----------------
if "stage" not in st.session_state:
    st.session_state.stage = "instructions"
if "practice_trials" not in st.session_state:
    st.session_state.practice_trials = make_block(PRACTICE_TRIALS, cong_prop=CONGRUENT_PROPORTION)
if "test_trials" not in st.session_state:
    st.session_state.test_trials = make_block(TRIALS_TOTAL, cong_prop=CONGRUENT_PROPORTION)
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "results" not in st.session_state:
    st.session_state.results = []
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "using_keyboard" not in st.session_state:
    st.session_state.using_keyboard = False  # user can enable later

st.set_page_config(page_title="Stroopy", layout="centered")

st.title("Stroopy — Color–Word Stroop Test")
st.write("Task: ignore the word text and **select the ink color** as fast and accurately as possible.")

# ---------------- Instructions ----------------
if st.session_state.stage == "instructions":
    st.header("Instructions")
    st.markdown(
        """
        - You will see a color word (RED, GREEN, BLUE, YELLOW) displayed in colored ink.
        - Your task: **select the color of the ink**, not the word text.
        - Prefer using keyboard (R/G/B/Y) for speed. If keyboard isn't available, use the big buttons.
        - We will run a few practice trials first, then the test block.
        - Try to be both fast and accurate.
        """
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Practice"):
            st.session_state.stage = "practice"
            st.session_state.current_idx = 0
            st.session_state.results = []
            st.session_state.start_time = None
    with col2:
        using_kb = st.checkbox("Prefer keyboard (R/G/B/Y) when available", value=False)
        st.session_state.using_keyboard = using_kb

    st.markdown("**Note:** This app works fully with buttons. Keyboard support can be enabled (see comments in the code).")

# ---------------- Practice ----------------
elif st.session_state.stage == "practice":
    st.header("Practice Trials")
    idx = st.session_state.current_idx
    trials = st.session_state.practice_trials
    if idx >= len(trials):
        st.success("Practice finished.")
        if st.button("Proceed to Test"):
            st.session_state.stage = "test"
            st.session_state.current_idx = 0
            st.session_state.start_time = None
    else:
        trial = trials[idx]
        st.write(f"Practice {idx+1} / {len(trials)}")
        show_stimulus(trial)

        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()
            st.session_state.current_onset = st.session_state.start_time

        cols = st.columns(4)
        for i, color in enumerate(COLOR_NAMES):
            if cols[i].button(color):
                rt = time.time() - st.session_state.start_time
                rt = None if rt > MAX_RT else rt
                record_response(st.session_state.results, trial, color[0], rt, practice=True)
                st.session_state.current_idx += 1
                st.session_state.start_time = None
                st.rerun()

# ---------------- Test ----------------
elif st.session_state.stage == "test":
    st.header("Test")
    idx = st.session_state.current_idx
    trials = st.session_state.test_trials
    total = len(trials)
    if idx >= total:
        st.session_state.stage = "finished"
        st.rerun()
    else:
        trial = trials[idx]
        st.write(f"Trial {idx+1} / {total}")
        show_stimulus(trial)

        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()
            st.session_state.current_onset = st.session_state.start_time

        if st.session_state.using_keyboard:
            st.info("Press R (red), G (green), B (blue), Y (yellow) — or use the buttons below.")

        cols = st.columns(4)
        clicked = None
        for i, color in enumerate(COLOR_NAMES):
            if cols[i].button(color):
                clicked = color[0]
        if clicked:
            rt = time.time() - st.session_state.start_time
            if rt < MIN_VALID_RT:
                rt_val = rt
            else:
                rt_val = rt if rt <= MAX_RT else None
            record_response(st.session_state.results, trial, clicked, rt_val, practice=False)
            time.sleep(ISI)
            st.session_state.current_idx += 1
            st.session_state.start_time = None
            st.rerun()

        try:
            from streamlit_js_eval import streamlit_js_eval
            js_code = """
            (function(){
                try {
                    if (!document.body.hasAttribute('tabindex')) {
                        document.body.setAttribute('tabindex', '-1');
                    }
                    document.body.focus();
                    window.focus && window.focus();
                } catch(e) {}

                if (!window._stroop_setup) {
                    window._stroop_setup = true;
                    window._stroop_key = null;
                    window._stroop_onset = null;
                    document.addEventListener('keydown', (e) => {
                        const k = ('' + e.key).toUpperCase();
                        if (['R','G','B','Y'].includes(k) && !window._stroop_key) {
                            window._stroop_key = k;
                            window._stroop_onset = performance.now();
                        }
                    });
                }
                if (window._stroop_key) {
                    return JSON.stringify({k: window._stroop_key, t: window._stroop_onset});
                }
                return null;
            })()
            """
            js_result = streamlit_js_eval(js_expressions=js_code, key="stroop_key_listener")
            if js_result:
                try:
                    import json
                    parsed = json.loads(js_result)
                    key = parsed.get("k")
                except Exception:
                    key = js_result
                rt = time.time() - st.session_state.start_time
                record_response(st.session_state.results, trial, key, rt if rt<=MAX_RT else None, practice=False)
                time.sleep(ISI)
                st.session_state.current_idx += 1
                st.session_state.start_time = None
                streamlit_js_eval(js_expressions="window._stroop_key = null; window._stroop_onset = null;", key="stroop_key_clear")
                st.rerun()
        except Exception:
            pass

# ---------------- Finished & Results ----------------
elif st.session_state.stage == "finished":
    st.header("Results")
    df = pd.DataFrame(st.session_state.results)
    if df.empty:
        st.info("No data collected.")
    else:
        test_df = df[df["practice"] == False].copy()
        test_df["rt_s_clean"] = test_df["rt_s"].where(test_df["rt_s"].notnull() & (test_df["rt_s"] >= MIN_VALID_RT))
        
        overall_acc = test_df["correct"].mean() * 100 if not test_df.empty else 0
        overall_rt = test_df["rt_s_clean"].mean() if not test_df.empty else None
        cong_df = test_df[test_df["congruent"] == True]
        incong_df = test_df[test_df["congruent"] == False]
        cong_rt = cong_df["rt_s_clean"].mean() if not cong_df.empty else None
        incong_rt = incong_df["rt_s_clean"].mean() if not incong_df.empty else None
        cong_acc = cong_df["correct"].mean() * 100 if not cong_df.empty else None
        incong_acc = incong_df["correct"].mean() * 100 if not incong_df.empty else None
        stroop_effect = None
        if cong_rt is not None and incong_rt is not None:
            stroop_effect = incong_rt - cong_rt

        st.metric("Overall accuracy (%)", f"{overall_acc:.1f}")
        st.metric("Overall mean RT (s)", f"{overall_rt:.3f}" if overall_rt else "N/A")
        st.write("### By condition")
        st.write({
            "congruent_mean_rt_s": cong_rt,
            "incongruent_mean_rt_s": incong_rt,
            "congruent_acc_%": cong_acc,
            "incongruent_acc_%": incong_acc,
            "stroop_interference_s (incong - cong)": stroop_effect
        })

        # ---- Cognitive decline judgment ----
        decline_flag = False
        reasons = []
        if overall_acc < 70:
            decline_flag = True
            reasons.append("Low accuracy (<70%)")
        if overall_rt and overall_rt > 2.0:
            decline_flag = True
            reasons.append("Slow reaction time (>2s)")
        if stroop_effect and stroop_effect > 0.7:
            decline_flag = True
            reasons.append("High Stroop interference (>0.7s)")

        if decline_flag:
            st.error(f"⚠️ Possible cognitive decline detected. Reasons: {', '.join(reasons)}")
        else:
            st.success("✅ No cognitive decline detected. Performance within normal limits.")

        st.write("### Trial-level data (test trials)")
        st.dataframe(test_df.reset_index(drop=True))

        csv = test_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download test results (CSV)", data=csv, file_name="stroopy_results.csv", mime="text/csv")

    if st.button("Restart entire session"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

import json
from dataclasses import asdict
from typing import List, Optional

import streamlit as st

from core.dialog import DialogManager
from core.stream import VideoFileStreamer
from core.vqa_engine import VQAEngine


def _parse_times(times_text: str) -> List[float]:
    return [float(t.strip()) for t in times_text.split(",") if t.strip()]


def _parse_questions(questions_text: str) -> List[str]:
    return [q.strip() for q in questions_text.split("|") if q.strip()]


def main():
    st.set_page_config(page_title="Ambiguity-Aware VQA (Accessible)", layout="centered")
    st.title("Ambiguity-Aware VQA (Accessible Web App)")
    st.caption(
        "Accessibility: All inputs are labeled and the output blocks are stable for screen readers. "
        "Keyboard users can navigate with Tab/Shift+Tab in the order shown below."
    )

    with st.form("vqa_form"):
        st.subheader("Inputs")
        st.markdown("**Keyboard navigation order:** Video file → Question → Mode → FPS → Timestamps → Window → Run")
        uploaded = st.file_uploader(
            "Video file (mp4/mov/avi)",
            type=["mp4", "mov", "avi"],
            help="Upload a short video file for analysis.",
        )
        question = st.text_input(
            "Question (use | to separate per timestamp)",
            "",
            help="Example: 'What is on the table?|Which bowl has milk?'",
        )
        mode = st.selectbox(
            "Mode",
            ["one-pass", "iterative"],
            help="One-pass gives all info at once; iterative asks clarification questions.",
        )
        fps = st.number_input(
            "Sampling FPS",
            min_value=0.1,
            max_value=5.0,
            value=1.0,
            step=0.1,
            help="Frames per second sampled from the video.",
        )
        times_text = st.text_input(
            "Timestamps (seconds, comma-separated)",
            "",
            help="Example: 1,13. Leave empty to analyze the whole video.",
        )
        window = st.number_input(
            "Window length per timestamp (seconds)",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.5,
            help="Seconds of context per timestamp.",
        )
        run_clicked = st.form_submit_button("Run")

    if run_clicked and uploaded and question:
        temp_path = f"data/tmp_{uploaded.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded.read())

        streamer = VideoFileStreamer(temp_path, target_fps=float(fps), max_width=1280)
        engine = VQAEngine()
        dialog = DialogManager(engine)

        st.session_state["engine"] = engine
        st.session_state["dialog"] = dialog
        st.session_state["temp_path"] = temp_path
        st.session_state["mode"] = mode
        st.session_state["current_idx"] = 0
        st.session_state["responses"] = []
        st.session_state["frame_sets"] = []
        st.session_state["times"] = []
        st.session_state["questions"] = []

        if times_text.strip():
            times = _parse_times(times_text)
            questions = _parse_questions(question)
            if not questions:
                questions = [question] * len(times)
            if len(questions) < len(times):
                questions += [questions[-1]] * (len(times) - len(questions))

            frame_sets = streamer.collect_frames_at_times(times, window_s=float(window))
            st.session_state["times"] = times
            st.session_state["questions"] = questions
            st.session_state["frame_sets"] = frame_sets
            st.session_state["responses"] = [None] * len(times)
        else:
            if "|" in question:
                st.error("Multiple questions detected. Please provide timestamps with --times.")
                return
            frames = streamer.collect_frames(duration_s=None)
            st.session_state["times"] = [None]
            st.session_state["questions"] = [question]
            st.session_state["frame_sets"] = [frames]
            st.session_state["responses"] = [None]

    if "frame_sets" in st.session_state:
        dialog: Optional[DialogManager] = st.session_state.get("dialog")
        mode = st.session_state.get("mode", "one-pass")
        times = st.session_state.get("times", [])
        questions = st.session_state.get("questions", [])
        frame_sets = st.session_state.get("frame_sets", [])
        responses = st.session_state.get("responses", [])

        idx = st.session_state.get("current_idx", 0)
        if idx >= len(frame_sets):
            st.success("All timestamps processed.")
            return

        t = times[idx] if idx < len(times) else None
        q = questions[idx] if idx < len(questions) else ""
        frames = frame_sets[idx]

        st.subheader(f"Timestamp: {t:.1f}s" if t is not None else "Full video")
        st.write(f"Question: {q}")

        if responses[idx] is None:
            if mode == "iterative":
                first = dialog.iterative_first(frames, q)
                responses[idx] = {"turns": [first]}
            else:
                resp = dialog.one_pass(frames, q)
                responses[idx] = {"turns": [resp]}

        turns = responses[idx]["turns"]
        for turn_idx, resp in enumerate(turns, start=1):
            st.markdown(f"**Response {turn_idx}**")
            st.write(resp.response)
            st.code(json.dumps(asdict(resp), ensure_ascii=False, indent=2))

        last_resp = turns[-1]
        if mode == "iterative" and last_resp.ambiguity:
            st.markdown("**Clarification needed**")
            clarify_key = f"clarify_{idx}_{len(turns)}"
            clarify_text = st.text_input(
                "Your clarification",
                key=clarify_key,
                help="Example: 'the patterned bowl' or 'the one with milk'",
            )
            if st.button("Submit clarification", key=f"clarify_btn_{idx}_{len(turns)}"):
                followup = dialog.iterative_followup(frames, q, clarify_text)
                turns.append(followup)
                responses[idx]["turns"] = turns
                st.session_state["responses"] = responses
                st.rerun()
        else:
            if st.button("Next timestamp", key=f"next_{idx}"):
                st.session_state["current_idx"] = idx + 1
                st.session_state["responses"] = responses
                st.rerun()

        st.session_state["responses"] = responses


if __name__ == "__main__":
    main()


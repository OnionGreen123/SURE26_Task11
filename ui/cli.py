import argparse
from typing import Optional

from config import settings
from core.dialog import DialogManager
from core.stream import VideoFileStreamer, VideoStream
from core.vqa_engine import VQAEngine
from ui.logger import RunLogger


def _get_clarification(question: str, model_prompt: str) -> str:
    print(f"\nClarification needed for question: {question}", flush=True)
    if model_prompt:
        print(f"Model asked: {model_prompt}", flush=True)
    return input("Clarify > ").strip()


def run_cli(
    video_path: Optional[str],
    camera_index: Optional[int],
    question: str,
    mode: str,
    fps: float,
    seconds: Optional[float],
    stream: bool,
    times: Optional[str],
    window: float,
    questions: Optional[str],
    max_turns: int,
):
    logger = RunLogger()
    if not video_path:
        raise SystemExit("This prototype expects a video file. Provide --video.")
    stream_source = VideoStream(video_path=video_path, camera_index=camera_index)
    streamer = None
    try:
        engine = VQAEngine()
        dialog = DialogManager(engine)

        streamer = VideoFileStreamer(video_path, target_fps=fps, max_width=settings.MAX_WIDTH)
        if times:
            time_list = [float(t.strip()) for t in times.split(",") if t.strip()]
            question_list = []
            if questions:
                question_list = [q.strip() for q in questions.split("|") if q.strip()]
            elif "|" in question:
                question_list = [q.strip() for q in question.split("|") if q.strip()]
            if not question_list:
                question_list = [question] * len(time_list)
            if len(question_list) < len(time_list):
                question_list += [question_list[-1]] * (len(time_list) - len(question_list))
            frame_sets = streamer.collect_frames_at_times(time_list, window_s=window)
            for idx, (t, frames) in enumerate(zip(time_list, frame_sets), start=1):
                current_question = question_list[idx - 1]
                if mode == "iterative":
                    responses = []
                    first = dialog.iterative_first(frames, current_question)
                    responses.append(first)
                    for idx, resp in enumerate(responses, start=1):
                        logger.log(
                            "iterative_turn",
                            {"time_s": t, "question": current_question, "turn": idx, "raw": resp.raw_text},
                        )
                        print(f"\n=== Response {idx} (t={t}s) ===\n")
                        print(resp.raw_text)
                    turn = 1
                    while responses[-1].ambiguity and turn < max_turns:
                        clarification = _get_clarification(current_question, responses[-1].response)
                        followup = dialog.iterative_followup(frames, current_question, clarification)
                        responses.append(followup)
                        turn += 1
                        logger.log(
                            "iterative_turn",
                            {"time_s": t, "question": current_question, "turn": turn, "raw": followup.raw_text},
                        )
                        print(f"\n=== Response {turn} (t={t}s) ===\n")
                        print(followup.raw_text)
                else:
                    resp = dialog.one_pass(frames, current_question)
                    logger.log("one_pass", {"time_s": t, "question": current_question, "raw": resp.raw_text})
                    print(f"\n=== Response (t={t}s) ===\n")
                    print(resp.raw_text)
        else:
            frames = streamer.collect_frames(duration_s=None)
            if mode == "iterative":
                responses = []
                first = dialog.iterative_first(frames, question)
                responses.append(first)
                logger.log("iterative_turn", {"turn": 1, "raw": first.raw_text})
                print("\n=== Response 1 ===\n")
                print(first.raw_text)
                turn = 1
                while responses[-1].ambiguity and turn < max_turns:
                    clarification = _get_clarification(question, responses[-1].response)
                    followup = dialog.iterative_followup(frames, question, clarification)
                    responses.append(followup)
                    turn += 1
                    logger.log("iterative_turn", {"turn": turn, "raw": followup.raw_text})
                    print(f"\n=== Response {turn} ===\n")
                    print(followup.raw_text)
            else:
                resp = dialog.one_pass(frames, question)
                logger.log("one_pass", {"raw": resp.raw_text})
                print("\n=== Response ===\n")
                print(resp.raw_text)
            if mode == "iterative":
                first, second = dialog.iterative(frames, question, _get_clarification)
                logger.log("iterative_first", {"raw": first.raw_text})
                print("\n=== First Response ===\n")
                print(first.raw_text)
                if second:
                    logger.log("iterative_second", {"raw": second.raw_text})
                    print("\n=== Second Response ===\n")
                    print(second.raw_text)
            else:
                resp = dialog.one_pass(frames, question)
                logger.log("one_pass", {"raw": resp.raw_text})
                print("\n=== Response ===\n")
                print(resp.raw_text)

    finally:
        stream_source.close()
        if streamer:
            streamer.close()
        logger.save()


def main():
    parser = argparse.ArgumentParser(description="Ambiguity-aware VQA CLI")
    parser.add_argument("--video", help="Video file path", default=None)
    parser.add_argument("--camera", type=int, help="(unused) camera index", default=None)
    parser.add_argument("--question", required=True, help="User question")
    parser.add_argument("--mode", choices=["one-pass", "iterative"], default="one-pass")
    parser.add_argument("--fps", type=float, default=settings.DEFAULT_FPS)
    parser.add_argument(
        "--seconds",
        type=float,
        default=None,
        help="(unused) kept for compatibility",
    )
    parser.add_argument("--stream", action="store_true", help="(unused) kept for compatibility")
    parser.add_argument("--times", type=str, default=None, help="Comma-separated timestamps (seconds)")
    parser.add_argument("--window", type=float, default=2.0, help="Seconds per timestamp window")
    parser.add_argument("--questions", type=str, default=None, help="Use '|' to separate questions per timestamp")
    parser.add_argument("--max-turns", type=int, default=3, help="Max clarification turns")

    args = parser.parse_args()
    if not args.video:
        raise SystemExit("Provide --video.")

    run_cli(
        video_path=args.video,
        camera_index=args.camera,
        question=args.question,
        mode=args.mode,
        fps=args.fps,
        seconds=args.seconds,
        stream=args.stream,
        times=args.times,
        window=args.window,
        questions=args.questions,
        max_turns=args.max_turns,
    )


if __name__ == "__main__":
    main()


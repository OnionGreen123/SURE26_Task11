## Project #11 - Ambiguity-Aware VQA Web App

### Setup
1) Create and activate a virtual environment.
2) Install dependencies:
   - `pip install -r requirements.txt`
3) Set your API key:
   - Windows PowerShell: `setx GOOGLE_API_KEY "YOUR_KEY"`
   - Or set `GOOGLE_API_KEY` in your shell.

### Run (Web App)
`streamlit run app.py`

### Web App Usage
1) Upload a video file (mp4/mov/avi).
2) Choose mode:
   - **one-pass**: full response in one turn.
   - **iterative**: clarification questions until ambiguity is resolved.
3) Set timestamps (optional):
   - Use `Timestamps` as comma-separated seconds, e.g., `1,13`.
   - Use `Question` with `|` to provide one question per timestamp.
4) Click **Run** to start.
5) In iterative mode, answer clarification prompts until resolved, then click **Next timestamp**.

### Run (CLI)
Example (video file):
`python -m scripts.run_cli --video "path/to/video.mp4" --question "What is on the table?"`

Example (per-timestamp questions):
`python -m scripts.run_cli --video "path/to/video.mp4" --times "1,13" --questions "Q1|Q2"`

### Notes
- This prototype uses **non-live** Gemini models (no Live API required).
- Input is a **static video file**; frames are sampled and sent to the model.
- Responses are text-only and structured in JSON-like output.
- Two modes: `one-pass` and `iterative`.


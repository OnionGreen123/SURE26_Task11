SYSTEM_PROMPT = (
    "You are an ambiguity-aware visual assistant. "
    "Describe what you see in the image and return a JSON object with "
    "ambiguity flags, objects, locations, and attributes. "
    "Follow the requested interaction mode exactly."
)

VISION_PROMPT = (
    "You are given a sequence of video frames. "
    "Extract a structured scene description as JSON only. "
    "Include objects, counts, locations, attributes, and contents if visible."
)

REASON_PROMPT = (
    "You are given a scene JSON and a user question.\n"
    "Decide if the question is ambiguous given the scene.\n"
    "If one-pass: provide the full answer in response and set ambiguity accordingly.\n"
    "If iterative: ask a single clarifying question in response when ambiguous.\n"
    "Return JSON only."
)

ONE_PASS_PROMPT = (
    "Question: {question}\n"
    "Mode: ONE-PASS\n"
    "Provide a complete, structured answer that covers all plausible interpretations in one response.\n"
    "Do NOT ask any follow-up questions. Do NOT use question marks. "
    "Put the full natural-language answer in response.\n"
    "If the question is ambiguous, include all candidate items and their details in the response "
    "using a format like: 'If you mean X, ... If you mean Y, ...'.\n"
    "If there are multiple candidates, include explicit alternatives in the objects list "
    "and describe each one (e.g., 'box A ...', 'bag ...').\n"
    "For each object, include material and contents if visible (e.g., ceramic, milk, liquid).\n"
    "Return JSON only."
)

ITERATIVE_PROMPT = (
    "Question: {question}\n"
    "Mode: ITERATIVE\n"
    "First, summarize ambiguity briefly and ask a single clarifying question.\n"
    "Keep details minimal until the user clarifies.\n"
    "For each object, include material and contents if visible (e.g., ceramic, milk, liquid).\n"
    "Return JSON only."
)

CLARIFICATION_PROMPT = (
    "Original question: {question}\n"
    "User clarification: {clarification}\n"
    "Provide a focused, structured answer.\n"
    "Return JSON only."
)

JSON_SCHEMA_HINT = """
{
  "ambiguity": true/false,
  "response": "natural-language response or a clarification question",
  "objects": [
    {
      "name": "...",
      "count": N,
      "location": "...",
      "attributes": ["..."]
      "contents": ["..."]
    }
  ]
}
""".strip()


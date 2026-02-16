from typing import Optional

from google import genai
from google.genai import types

from config import prompts, settings


class VQAEngine:
    def __init__(self, model: Optional[str] = None):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not set.")
        self.model = model or settings.MODEL
        self.text_model = settings.TEXT_MODEL
        self.client = genai.Client(http_options={"api_version": settings.API_VERSION})

    def run_vision_extract(self, frames) -> str:
        system_text = f"{prompts.VISION_PROMPT}\n\n{prompts.JSON_SCHEMA_HINT}"
        contents = list(frames) + ["Extract the scene JSON now."]
        config = types.GenerateContentConfig(
            system_instruction=system_text,
            response_mime_type=settings.RESPONSE_MIME_TYPE,
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
        return (response.text or "").strip()

    def run_text_reasoner(
        self,
        scene_json: str,
        question: str,
        mode: str,
        clarification: Optional[str] = None,
    ) -> str:
        if mode == "iterative":
            mode_prompt = prompts.ITERATIVE_PROMPT.format(question=question)
        elif mode == "clarify":
            mode_prompt = prompts.CLARIFICATION_PROMPT.format(
                question=question, clarification=clarification or ""
            )
        else:
            mode_prompt = prompts.ONE_PASS_PROMPT.format(question=question)

        system_text = f"{prompts.REASON_PROMPT}\n\n{prompts.JSON_SCHEMA_HINT}"
        user_prompt = f"Scene JSON:\n{scene_json}\n\n{mode_prompt}"

        config = types.GenerateContentConfig(
            system_instruction=system_text,
            response_mime_type=settings.RESPONSE_MIME_TYPE,
        )
        response = self.client.models.generate_content(
            model=self.text_model,
            contents=[user_prompt],
            config=config,
        )
        return (response.text or "").strip()

    def run_query(
        self,
        frames,
        question: str,
        mode: str,
        clarification: Optional[str] = None,
    ) -> str:
        scene_json = self.run_vision_extract(frames)
        return self.run_text_reasoner(scene_json, question, mode, clarification)


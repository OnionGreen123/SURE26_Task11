from typing import Callable, Optional, Tuple

from core.ambiguity import append_ambiguity_reason, parse_response
from core.schemas import VQAResponse


class DialogManager:
    def __init__(self, engine):
        self.engine = engine

    def one_pass(self, frames, question: str) -> VQAResponse:
        text = self.engine.run_query(frames, question, mode="one-pass")
        resp = parse_response(text)
        resp = append_ambiguity_reason(resp)
        if not resp.response:
            resp.response = resp.raw_text
        return resp

    def iterative_first(self, frames, question: str) -> VQAResponse:
        first_text = self.engine.run_query(frames, question, mode="iterative")
        first_resp = parse_response(first_text)
        first_resp = append_ambiguity_reason(first_resp)
        if not first_resp.response:
            first_resp.response = first_resp.raw_text
        return first_resp

    def iterative_followup(
        self,
        frames,
        question: str,
        clarification: str,
    ) -> VQAResponse:
        second_text = self.engine.run_query(
            frames, question, mode="clarify", clarification=clarification
        )
        second_resp = parse_response(second_text)
        if not second_resp.response:
            second_resp.response = second_resp.raw_text
        return second_resp

    def iterative_loop(
        self,
        frames,
        question: str,
        clarification_provider: Callable[[], str],
        max_turns: int = 3,
    ):
        responses = []
        first = self.iterative_first(frames, question)
        responses.append(first)
        turns = 1
        while first.ambiguity and turns < max_turns:
            clarification = clarification_provider()
            followup = self.iterative_followup(frames, question, clarification)
            responses.append(followup)
            if not followup.ambiguity:
                break
            first = followup
            turns += 1
        return responses


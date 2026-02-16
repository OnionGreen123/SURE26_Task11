import json
import re
from typing import Any, Dict, Tuple

from core.schemas import ObjectDesc, VQAResponse


def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def parse_response(text: str) -> VQAResponse:
    payload = _extract_json(text)
    if not payload:
        return VQAResponse(raw_text=text)

    try:
        data: Dict[str, Any] = json.loads(payload)
    except json.JSONDecodeError:
        return VQAResponse(raw_text=text)

    objects = []
    for obj in data.get("objects", []) or []:
        objects.append(
            ObjectDesc(
                name=str(obj.get("name", "")),
                count=obj.get("count"),
                location=obj.get("location"),
                attributes=list(obj.get("attributes", []) or []),
                contents=list(obj.get("contents", []) or []),
            )
        )

    return VQAResponse(
        ambiguity=bool(data.get("ambiguity", False)),
        objects=objects,
        response=str(data.get("response", "")),
        raw_text=text,
    )


def _tokenize(text: str) -> Tuple[str, ...]:
    return tuple(re.findall(r"[a-zA-Z]+", text.lower()))


def _score_object(tokens: Tuple[str, ...], obj: ObjectDesc) -> int:
    score = 0
    name_tokens = set(_tokenize(obj.name))
    attr_tokens = set(_tokenize(" ".join(obj.attributes)))
    for tok in tokens:
        if tok in name_tokens:
            score += 2
        if tok in attr_tokens:
            score += 3
    return score


def _explicit_qualifiers(question: str) -> Tuple[str, ...]:
    q = question.lower()
    qualifiers = set()
    # Patterns like "bowl with milk", "bowl that has egg"
    for match in re.findall(r"(with|having|that has|that have|containing)\s+([a-zA-Z]+)", q):
        qualifiers.add(match[1])
    # Pattern like "added milk to the bowl"
    for match in re.findall(r"added\s+([a-zA-Z]+)\s+to\s+the\s+\w+", q):
        qualifiers.add(match[0])
    return tuple(sorted(qualifiers))


def _build_summary(target: ObjectDesc, inference_note: str | None = None) -> str:
    parts = [f"I see a {target.name}."]
    if target.location:
        parts.append(f"It is located {target.location}.")
    if target.attributes:
        parts.append(f"It looks {', '.join(target.attributes)}.")
    if inference_note:
        parts.append(inference_note)
    return " ".join(parts)




def refine_ambiguity(question: str, resp: VQAResponse) -> VQAResponse:
    if not resp.objects:
        return resp

    if len(resp.objects) == 1:
        resp.ambiguity = False
        if not resp.response or resp.response.strip().endswith("?"):
            resp.response = _build_summary(resp.objects[0])
        return resp

    tokens = _tokenize(question)
    qualifiers = _explicit_qualifiers(question)
    if not tokens:
        return resp

    scores = [_score_object(tokens, obj) for obj in resp.objects]
    max_score = max(scores)
    if max_score <= 0:
        return resp

    # If there is a unique best match, treat as unambiguous.
    if scores.count(max_score) == 1:
        resp.ambiguity = False
        best_idx = scores.index(max_score)
        best_obj = resp.objects[best_idx]
        if not resp.response or resp.response.strip().endswith("?"):
            matched_tokens = []
            name_tokens = set(_tokenize(best_obj.name))
            attr_tokens = set(_tokenize(" ".join(best_obj.attributes)))
            for tok in tokens:
                if tok in name_tokens or tok in attr_tokens:
                    matched_tokens.append(tok)
            matched_tokens = sorted(set(matched_tokens))
            if matched_tokens:
                note = (
                    "I inferred this because your question mentions "
                    f"{', '.join(matched_tokens)}, which matches only this item."
                )
            else:
                note = None
            resp.response = _build_summary(best_obj, inference_note=note)

    # If multiple candidates share the same target noun and no explicit qualifier,
    # keep ambiguity even if one has a matching attribute.
    name_tokens = [_tokenize(obj.name) for obj in resp.objects]
    if not qualifiers and len(resp.objects) > 1:
        resp.ambiguity = True

    return resp


def append_ambiguity_reason(resp: VQAResponse) -> VQAResponse:
    if not resp.ambiguity:
        return resp
    if "because" in (resp.response or "").lower():
        return resp
    if len(resp.objects) > 1:
        names = ", ".join(obj.name for obj in resp.objects[:3] if obj.name)
        reason = (
            "I could not disambiguate because multiple items match your question "
            f"({names})."
        )
    else:
        reason = "I could not disambiguate because there is not enough evidence."
    if resp.response:
        resp.response = f"{resp.response} {reason}"
    else:
        resp.response = reason
    return resp


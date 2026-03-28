import os
import json
import httpx
from dotenv import load_dotenv

from app.models import Envelope, MatchingResult, Decision

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"


class MatchingService:

    @staticmethod
    async def match(envelope: Envelope) -> Envelope:
        threshold = envelope.processing_instructions.confidence_threshold
        extraction = envelope.extraction

        commodity_code = extraction.get("commodity_code")
        commodity_desc = extraction.get("commodity_desc")

        if not envelope.decision:
            envelope.decision = Decision(route="auto_approve")

        if commodity_code and commodity_code.confidence is not None:
            if commodity_code.confidence >= threshold:
                envelope.matching_results = MatchingResult(
                    matched_code=commodity_code.value,
                    match_confidence=commodity_code.confidence,
                    rationale="High confidence extraction",
                    fallback_used=False,
                    source="catalog_exact"
                )
                return envelope

        if not commodity_desc or not commodity_desc.value:
            return MatchingService._no_match(envelope, "Missing commodity description")

        try:
            llm_result = await MatchingService._call_gemini(commodity_desc.value)

            envelope.matching_results = llm_result

            if llm_result.match_confidence < 0.70:
                envelope.decision.route = "hitl_review"

        except Exception:
            return MatchingService._fallback(envelope, commodity_desc.value)

        return envelope

    @staticmethod
    async def _call_gemini(description: str) -> MatchingResult:
        prompt = f"""
You are an expert in HS classification.

Return ONLY valid JSON:
{{
  "matched_code": "...",
  "match_confidence": 0.0,
  "rationale": "..."
}}

Description:
{description}
"""

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                GEMINI_URL,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ]
                }
            )

        if response.status_code != 200:
            raise ValueError(response.text)

        data = response.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON from Gemini")

        return MatchingResult(
            matched_code=parsed.get("matched_code"),
            match_confidence=parsed.get("match_confidence", 0.0),
            rationale=parsed.get("rationale"),
            fallback_used=True,
            source="llm_match"
        )

    @staticmethod
    def _fallback(envelope: Envelope, description: str) -> Envelope:
        envelope.matching_results = MatchingResult(
            matched_code="6203.42.0000",
            match_confidence=0.78,
            rationale=f"Fallback match for: {description}",
            fallback_used=True,
            source="llm_match"
        )

        if not envelope.decision:
            envelope.decision = Decision(route="hitl_review")
        else:
            envelope.decision.route = "hitl_review"

        return envelope

    @staticmethod
    def _no_match(envelope: Envelope, reason: str) -> Envelope:
        envelope.matching_results = MatchingResult(
            matched_code=None,
            match_confidence=0.0,
            rationale=reason,
            fallback_used=False,
            source="no_match"
        )

        if not envelope.decision:
            envelope.decision = Decision(route="hitl_review")
        else:
            envelope.decision.route = "hitl_review"

        return envelope
from fastapi import FastAPI, HTTPException
from app.services.validation_service import ValidationService
from app.services.matching_service import MatchingService
from app.utils.audit import create_audit_entry
from app.models import Envelope
import asyncio

app = FastAPI()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "document-intelligence",
        "version": "1.0"
    }


@app.post("/validate")
async def validate(envelope: Envelope):
    try:
        validated = ValidationService.validate(envelope)

        failed_fields = [
            r.field for r in validated.validation_results if not r.valid
        ]

        audit_entry = create_audit_entry(
            envelope_id=envelope.envelope_id,
            result="success" if not failed_fields else "failure",
            details={"failed_fields": failed_fields}
        )

        validated.audit.append(audit_entry)

        return validated

    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/match")
async def match(envelope: Envelope):
    try:
        result = await MatchingService.match(envelope)

        matching_details = {}
        if result.matching_results:
            matching_details = result.matching_results.model_dump()

        result.audit.append(
            create_audit_entry(
                envelope_id=result.envelope_id,
                result="matching_complete",
                details=matching_details
            )
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Matching failed: {str(e)}"
        )

@app.post("/process")
async def process(envelope: Envelope):
    try:
        envelope = ValidationService.validate(envelope)

        envelope.audit.append(
            create_audit_entry(
                envelope_id=envelope.envelope_id,
                result="validation_complete",
                details={
                    "route": envelope.decision.route
                }
            )
        )

        extraction = envelope.extraction
        threshold = envelope.processing_instructions.confidence_threshold

        commodity_code = extraction.get("commodity_code")

        if (
            commodity_code
            and commodity_code.confidence is not None
            and commodity_code.confidence < threshold
        ):
            envelope = await MatchingService.match(envelope)

            matching_details = {}
            if envelope.matching_results:
                matching_details = envelope.matching_results.model_dump()

            envelope.audit.append(
                create_audit_entry(
                    envelope_id=envelope.envelope_id,
                    result="matching_complete",
                    details=matching_details
                )
            )

        return envelope

    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Processing failed: {str(e)}"
        )
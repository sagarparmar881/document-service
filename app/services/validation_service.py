from datetime import datetime, timedelta
from typing import List

from app.models import Envelope, ValidationResult
from app.models import Decision


class ValidationService:

    @staticmethod
    def validate(envelope: Envelope) -> Envelope:
        results: List[ValidationResult] = []
        threshold = envelope.processing_instructions.confidence_threshold

        extraction = envelope.extraction

        # Required Fields
        required_fields = ["shipment_id", "recipient_name"]
        for field in required_fields:
            data = extraction.get(field)
            if not data or data.value is None or not str(data.value).strip():
                results.append(ValidationResult(field=field, valid=False, reason="Missing or empty field"))
            else:
                results.append(ValidationResult(field=field, valid=True))

        #  Commodity check
        if not extraction.get("commodity_code") and not extraction.get("commodity_desc"):
            results.append(
                ValidationResult(
                    field="commodity",
                    valid=False,
                    reason="At least one of commodity_code or commodity_desc required"
                )
            )

        #  Confidence check
        for field, data in extraction.items():
            if data and data.confidence is not None:
                if data.confidence < threshold:
                    results.append(
                        ValidationResult(
                            field=field,
                            valid=False,
                            reason=f"Low confidence ({data.confidence})"
                        )
                    )

        # Date validation
        ship_date_data = extraction.get("ship_date")
        if ship_date_data and ship_date_data.value:
            try:
                ship_date = datetime.strptime(ship_date_data.value, "%Y-%m-%d").date()
                today = datetime.utcnow().date()

                if ship_date > today:
                    results.append(ValidationResult(field="ship_date", valid=False, reason="Future date"))

                if ship_date < today - timedelta(days=365):
                    results.append(ValidationResult(field="ship_date", valid=False, reason="Too old"))
            except Exception:
                results.append(ValidationResult(field="ship_date", valid=False, reason="Invalid format"))

        #  Decision
        failed = any(not r.valid for r in results)

        if not failed:
            route = "auto_approve"
        elif envelope.processing_instructions.hitl_on_failure:
            route = "hitl_review"
        else:
            route = "rejected"

        envelope.validation_results = results
        envelope.decision = Decision(route=route)

        return envelope
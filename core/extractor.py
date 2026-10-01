import re
from typing import Optional
from pydantic import BaseModel, Field

class ExtractedInquiry(BaseModel):
    order_id: Optional[str] = Field(default=None, description="Extracted order reference, e.g. OMNI-1002")
    category: str = Field(default="general", description="Identified category: returns, shipping, warranty, pricing_promotion, general")
    issue_description: str = Field(..., description="Original raw customer query")
    discretionary_request: bool = Field(default=False, description="True if customer asks for unlisted/manual custom discount")

def extract_inquiry_details(query_text: str) -> ExtractedInquiry:
    """
    Extracts structured inquiry parameters from customer inputs using expanded semantic pattern rules.
    """
    q_lower = query_text.lower()

    # 1. Extract order reference
    order_match = re.search(r"(?:omni-?|#)?(\d{4})", q_lower)
    order_id = f"OMNI-{order_match.group(1)}" if order_match else None

    # 2. Comprehensive intent keyword sets
    returns_keywords = ["return", "refund", "exchange", "send back", "money back", "cancel", "unopened", "packaging", "cooling-off", "tailored", "bespoke"]
    shipping_keywords = ["shipping", "delivery", "postage", "carrier", "dpd", "royal mail", "highland", "islands", "surcharge", "lost", "transit", "courier", "cutoff", "next-day", "address", "rts", "doorstep", "tracking"]
    warranty_keywords = ["warranty", "broken", "fault", "defect", "damage", "dead", "doa", "repair", "battery", "crack", "water", "wear and tear", "screen", "power"]
    pricing_keywords = ["discount", "voucher", "promo", "code", "price match", "cheaper", "coupon", "nhs", "student", "stack"]

    # Category matching with priority scoring
    scores = {
        "returns": sum(1 for k in returns_keywords if k in q_lower),
        "shipping": sum(1 for k in shipping_keywords if k in q_lower),
        "warranty": sum(1 for k in warranty_keywords if k in q_lower),
        "pricing_promotion": sum(1 for k in pricing_keywords if k in q_lower)
    }

    best_cat = max(scores, key=scores.get)
    category = best_cat if scores[best_cat] > 0 else "general"

    # 3. Discretionary discount gap detection
    discretionary = False
    if category == "pricing_promotion":
        is_asking_discount = bool(re.search(r"\b(discount|off|deal|coupon|voucher|special price|cut)\b", q_lower))
        is_standard_promo = any(k in q_lower for k in ["student", "nhs", "price match", "blue light", "stack"])
        if is_asking_discount and not is_standard_promo:
            discretionary = True

    return ExtractedInquiry(
        order_id=order_id,
        category=category,
        issue_description=query_text,
        discretionary_request=discretionary
    )
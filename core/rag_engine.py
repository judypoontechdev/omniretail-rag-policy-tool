import os
import json
import anthropic
from core.config import ANTHROPIC_API_KEY
from core.vector_store import query_policy
from core.data_cleaner import get_order_by_id
from core.extractor import ExtractedInquiry

def generate_claude_response(query_text: str, context_snippets: list, order_info: dict, decision: str, gap_detected: str = None) -> str:
    """
    Directly invokes Anthropic Claude API using your verified model identifier
    to synthesize a context-grounded, legally compliant resolution.
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is not configured in environment or .env file.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    policy_context = "\n\n---\n\n".join(context_snippets) if context_snippets else "No specific policy clause retrieved."
    order_context_str = json.dumps(order_info, indent=2) if order_info else "No associated order found."

    system_instruction = (
        "You are an OmniRetail UK Senior Compliance and Operations Specialist. "
        "Your task is to draft a professional, courteous, and strictly compliant customer service response.\n"
        "- Base your decisions strictly on the retrieved policy context.\n"
        "- If a policy gap or discretionary discount denial exists, explain clearly why representatives are forbidden from applying custom manual discounts.\n"
        "- Always cite specific policy section numbers mentioned in the context.\n"
        "- Maintain a formal, courteous UK customer support tone."
    )

    user_prompt = f"""
Customer Inquiry: "{query_text}"

Internal System Evaluation:
- Preliminary Decision: {decision}
- Operational Gap Note: {gap_detected or 'None'}

Customer Order Record:
{order_context_str}

Retrieved Policy Reference Sections:
{policy_context}

Please provide the official customer resolution message based on the above information.
"""

    print(" Calling Anthropic Claude API (claude-haiku-4-5-20251001)...")

    # Call Claude Messages API with your verified available model
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        temperature=0.2,
        system=system_instruction,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.content[0].text.strip()


def run_rag_pipeline(inquiry: ExtractedInquiry) -> dict:
    """
    Executes end-to-end RAG reasoning:
    1. Looks up order fact history if order_id is present.
    2. Performs metadata-filtered ChromaDB vector search.
    3. Identifies operational gaps or strict policy conflicts.
    4. Synthesizes a factual, structured compliance response via Claude.
    """
    order_id = inquiry.order_id
    category = inquiry.category
    query_text = inquiry.issue_description
    discretionary = inquiry.discretionary_request

    # Step 1: Fact lookup
    order_info = get_order_by_id(order_id) if order_id else {}

    # Step 2: Vector search against policy manual
    retrieved = query_policy(query_text=query_text, category_filter=category, n_results=2)
    matched_sections = []
    context_snippets = []

    if retrieved.get("metadatas") and retrieved["metadatas"][0]:
        matched_sections = [m.get("section_title") for m in retrieved["metadatas"][0]]
        context_snippets = retrieved.get("documents", [[]])[0]

    # Step 3: Gap identification logic
    gap_detected = None
    decision = "Approved"

    if discretionary and category == "pricing_promotion":
        gap_detected = "Policy Section 16.1 & 16.2 strictly forbid customer service representatives from granting discretionary manual discounts."
        decision = "Gap / Denied"

    # Step 4: Live Claude generation call
    final_answer = generate_claude_response(
        query_text=query_text,
        context_snippets=context_snippets,
        order_info=order_info,
        decision=decision,
        gap_detected=gap_detected
    )

    return {
        "order_id": order_id,
        "order_info": order_info,
        "category": category,
        "decision": decision,
        "matched_sections": matched_sections,
        "gap_detected": gap_detected,
        "final_answer": final_answer
    }


if __name__ == "__main__":
    from core.extractor import extract_inquiry_details
    sample_query = "Can your rep give me a 10% manual discount on order OMNI-1002?"
    inquiry_obj = extract_inquiry_details(sample_query)
    output = run_rag_pipeline(inquiry_obj)
    print("\n=== Live Claude RAG Pipeline Test ===")
    print("Decision:", output["decision"])
    print("Final Answer:\n", output["final_answer"])
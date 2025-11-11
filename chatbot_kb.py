"""Structured in-app knowledge base for AI Assistant.

Provides deterministic answers for:
- Proposal development
- Website navigation
- Pricing & calculator
- Finding resources (templates, support, tools)

Usage:
from chatbot_kb import get_kb_answer
reply = get_kb_answer(user_text)

Design:
- Lightweight rule + keyword matcher (no external API dependency)
- Each article has: id, title, intent_tags, keywords, answer (HTML-ready), followups
- Fallback guides user to clarify
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Optional
import re

@dataclass
class KBArticle:
    id: str
    title: str
    intent_tags: List[str]
    keywords: List[str]
    answer: str
    followups: List[str]

# Core knowledge base entries
_KB: List[KBArticle] = [
    KBArticle(
        id="proposal_structure",
        title="Proposal Structure Essentials",
        intent_tags=["proposal","structure","technical","approach"],
        keywords=["technical approach","methodology","staffing","quality","transition"],
        answer=(
            "<strong>Standard Cleaning Contract Proposal Outline:</strong><br>"
            "1. Executive Summary – 1 page concise value proposition.<br>"
            "2. Understanding of Requirements – paraphrase objectives; confirm scope.<br>"
            "3. Technical Approach – methodology, workflows, specialty processes.<br>"
            "4. Staffing & Management – org chart, supervision ratios, training, background checks.<br>"
            "5. Quality Assurance – inspection cadence, KPIs, corrective actions.<br>"
            "6. Safety & Compliance – OSHA, green chemicals, infection control (medical).<br>"
            "7. Past Performance – 3–5 similar contracts with metrics (e.g., 98% inspection scores).<br>"
            "8. Transition & Mobilization – ramp plan days 0–30.<br>"
            "9. Pricing / Cost Narrative – assumptions, wage basis, escalation logic.<br>"
            "10. Differentiators – technology, responsiveness, specialty certifications.<br><br>"
            "<em>Tip:</em> Build a compliance matrix first and use it as your outline to avoid omissions."),
        followups=["Need a compliance matrix format?","Want staffing ratio examples?","Ask about quality KPIs"]
    ),
    KBArticle(
        id="past_performance",
        title="Past Performance Guidance",
        intent_tags=["proposal","past performance","references","experience"],
        keywords=["reference","performance","experience","similar","metrics"],
        answer=(
            "<strong>Effective Past Performance Sections:</strong><br>Provide 3–5 MOST RELEVANT contracts.<br><br>"
            "For each: Client name, period, annual value / sq ft, scope similarity, outcomes (metrics), client point of contact.<br>"
            "<em>Metrics examples:</em> 99.5% inspection pass, 15% supply cost reduction, 24/7 response under 30 mins.<br>"
            "Secure permission before listing references. Federal bids favor federal experience; if none, highlight scale and complexity from commercial/education/healthcare."),
        followups=["Need a template for a reference entry?","Want metric ideas?","Ask about differentiators"]
    ),
    KBArticle(
        id="pricing_strategy",
        title="Pricing & Cost Strategy",
        intent_tags=["pricing","cost","calculator","rate"],
        keywords=["labor","supplies","overhead","margin","wage","hourly"],
        answer=(
            "<strong>Pricing Components:</strong><br>Labor 70–80%, Supplies 5–10%, Equipment amortization, Overhead 12–20%, Profit 8–15%.<br>"
            "Check prevailing wage / locality adjustments. Use the <a href='/pricing-calculator'>Pricing Calculator</a> for multipliers (state & metro).<br>"
            "Healthy margins avoid being lowest bidder: too low = risk of non-compliance concerns.<br>"
            "<em>Tip:</em> Present a brief cost narrative: wage basis, supervision %, QA hours, escalation assumptions."),
        followups=["Want to estimate labor hours?","Ask about profit margin selection","Need calculator walkthrough?"]
    ),
    KBArticle(
        id="compliance_matrix",
        title="Compliance Matrix Basics",
        intent_tags=["compliance","matrix","requirements"],
        keywords=["compliance","matrix","requirement","section","page"],
        answer=(
            "<strong>Compliance Matrix Format:</strong><br>"
            "| RFP Section | Requirement Summary | Proposal Section | Page # |<br>"
            "Populate every mandatory item. Mark N/A only with justification. Track status (Draft / Complete).<br>"
            "Benefits: reduces risk of missed items, aids evaluator navigation, internal progress control."),
        followups=["Need a blank CSV version?","Ask how to prioritize missing items","Need transition plan guidance?"]
    ),
    KBArticle(
        id="navigation_help",
        title="Platform Navigation Overview",
        intent_tags=["navigation","where","find","locate","help"],
        keywords=["where","find","browse","contracts","leads","templates"],
        answer=(
            "<strong>Finding Things Quickly:</strong><br>Home cinematic landing → high-level overview.<br>"
            "Government: <a href='/federal-contracts'>Federal Contracts</a> (SAM.gov sourced).<br>"
            "Commercial: <a href='/commercial-contracts'>Commercial Properties</a> (property managers).<br>"
            "Supply & Quick Wins: <a href='/quick-wins'>Quick Wins & Supply</a> reverse marketplace.<br>"
            "AI Tools: Proposal generation (<a href='/ai-proposal-generator'>AI Proposal Generator</a>), Real-time proposal help (<a href='/ai-assistant'>AI Assistant</a>).<br>"
            "Templates: <a href='/proposal-templates'>Proposal Templates</a> for ready formats.<br>"
            "Pricing intelligence: <a href='/pricing-calculator'>Pricing Calculator</a> & <a href='/pricing-guide'>Pricing Guide</a>.<br>"
            "Support: Human consultation <a href='/proposal-support'>Proposal Support</a>."),
        followups=["Need federal vs commercial differences?","Ask about subscription benefits","Want lead saving instructions?"]
    ),
    KBArticle(
        id="proposal_templates",
        title="Using Proposal Templates",
        intent_tags=["templates","proposal","format"],
        keywords=["template","format","layout","sample"],
        answer=(
            "<strong>Template Workflow:</strong><br>1. Visit <a href='/proposal-templates'>Templates</a>.<br>"
            "2. Pick structure matching contract type (government, commercial, school, hospital).<br>"
            "3. Insert client-specific scope details & metrics.<br>"
            "4. Cross-check with compliance matrix before final formatting.<br>"
            "Samples illustrate tone; adapt not copy. Keep executive summary to 1 page."),
        followups=["Need executive summary tips?","Ask about differentiators section","Want past performance format?"]
    ),
    KBArticle(
        id="pricing_calculator_help",
        title="Pricing Calculator Walkthrough",
        intent_tags=["pricing","calculator","help","guide"],
        keywords=["calculator","multiplier","state","metro","labor","services"],
        answer=(
            "<strong>Calculator Steps:</strong><br>1. Enter facility sq ft & cleaning frequency.<br>"
            "2. Select state + metro area type (rural/suburban/urban/major).<br>"
            "3. Adjust service selections (floor care, power washing, etc.) to include add-ons.<br>"
            "4. Competition level modifies strategic discount/uplift (-7% to +7%).<br>"
            "5. Profit margin slider finalizes target margin (5–30%).<br>"
            "Output shows labor rate, monthly total, per-cleaning cost & national average comparison."),
        followups=["Need margin recommendation?","Ask how competition level works","Want example calculation?"]
    ),
    KBArticle(
        id="subscription_pricing",
        title="Subscription & WIN50 Discount",
        intent_tags=["pricing","subscription","discount","win50"],
        keywords=["win50","discount","subscription","price","monthly","annual"],
        answer=(
            "<strong>Current Promotion WIN50:</strong><br>Monthly: $49.50 (regular $99). Annual: $475 (regular $950).<br>"
            "Apply code WIN50 via banner or on <a href='/subscription'>Subscription</a>. Session tracks usage; backend switches billing plan IDs. Benefits: access to premium leads, proposal support tools, pricing intelligence."),
        followups=["Need help applying code?","Ask about plan differences","Want to know cancellation steps?"]
    ),
    # --- Role Expansion Articles ---
    KBArticle(
        id="role_research_assistant",
        title="Research Assistant Capabilities",
        intent_tags=["research","analyst","research assistant","data"],
        keywords=["market","trend","source","data","benchmark","industry"],
        answer=(
            "<strong>Research Assistant Mode:</strong><br>Use for gathering structured market context.<br>"
            "<em>Supported tasks:</em><br>• Summarize contract notice fields (agency, NAICS, set-aside).<br>"
            "• Suggest benchmark metrics (sq ft per FTE, cost per sq ft).<br>"
            "• Identify missing data points to strengthen a bid (e.g., green certifications).<br>"
            "<em>Limitations:</em> No live web crawling; relies on internal datasets and static KB references.<br>"
            "Ask: 'Research: average janitorial cost per sq ft in suburban VA' or 'Research: key differentiators for healthcare cleaning.'"),
        followups=["Ask benchmark labor ratios","Request NAICS explanation","Ask differentiators for sector"]
    ),
    KBArticle(
        id="role_economist",
        title="Economist / Pricing Intelligence",
        intent_tags=["economist","economic","rates","cost model"],
        keywords=["inflation","labor rate","wage","cost driver","margin","economic"],
        answer=(
            "<strong>Economist Mode:</strong><br>Focuses on cost structure sensitivity & macro factors.<br>"
            "Key levers: labor (70–80%), supply inflation (paper/plastics), regulatory compliance (prevailing wage), regional cost-of-living multipliers.<br>"
            "Scenario guidance: 'What if minimum wage rises 8%?' – adjust labor portion and recompute margin.<br>"
            "Use with pricing calculator for location multipliers and competition adjustments.<br>"
            "Provide: break-even analysis, margin range suggestions, impact of frequency changes.<br>"
            "Ask: 'Economist: effect of +10% labor cost on monthly total for 50K sq ft school 3x/week.'"),
        followups=["Ask break-even formula","Request margin optimization tips","Inquire inflation impact"]
    ),
    KBArticle(
        id="role_proposal_manager",
        title="Proposal Manager Guidance",
        intent_tags=["proposal manager","manager","proposal lead"],
        keywords=["schedule","timeline","kickoff","review","revision","submission"],
        answer=(
            "<strong>Proposal Manager Mode:</strong><br>Helps orchestrate the proposal lifecycle.<br>"
            "Phases:<br>1. Kickoff (requirements read-through + compliance matrix).<br>2. Drafting (technical, management, QA).<br>3. Review cycles (red team, gold team).<br>4. Final compliance sweep & formatting.<br>5. Submission readiness & backup plan.<br>"
            "Checklist emphasis: version control, page limits, mandatory forms, signatures, pricing consistency.<br>"
            "Ask: 'Proposal Manager: create 5-day rush schedule for 20-page RFP.'"),
        followups=["Ask rush schedule details","Request review cycle tips","Inquire checklist items"]
    ),
    KBArticle(
        id="role_it_support",
        title="IT / Platform Support",
        intent_tags=["it","support","technical","bug"],
        keywords=["login","error","cache","browser","performance","upload"],
        answer=(
            "<strong>IT Support Mode:</strong><br>Guides troubleshooting platform issues.<br>"
            "Common fixes:<br>• Clear browser cache & reload if layout broken.<br>• Ensure pop-ups allowed for payment flows.<br>• Large PDF failing? Reduce size / ensure under configured limit.<br>• Authentication expired? Sign out then back in.<br>"
            "Security reminder: Never share passwords; system stores minimal session data.<br>"
            "Ask: 'IT: why does my proposal upload stall?' or 'IT: fix pricing calculator not loading.'"),
        followups=["Ask file size limits","Request browser compatibility","Inquire session timeout"]
    ),
]

# Build fast lookup indexes
_INTENT_MAP: Dict[str, KBArticle] = {}
_KEYWORD_MAP: Dict[str, List[KBArticle]] = {}
for art in _KB:
    for tag in art.intent_tags:
        _INTENT_MAP[tag.lower()] = art
    for kw in art.keywords:
        _KEYWORD_MAP.setdefault(kw.lower(), []).append(art)

_WORD_RE = re.compile(r"[a-zA-Z0-9_-]+")

FALLBACK = (
    "I want to help but need a bit more detail. Please clarify if you're asking about pricing, proposal structure, navigation, templates, compliance, or past performance. You can also try: 'pricing strategy', 'technical approach outline', or 'where do I find templates'."
)

def get_kb_answer(user_text: str, role: Optional[str] = None) -> Dict[str, str]:
    """Return best KB answer and suggested follow-ups.
    Scoring: intent tag exact match > keyword match count > fallback.
    """
    cleaned = user_text.lower()

    # Direct intent tag match (allow role prefix shorthand e.g. 'economist:' )
    for tag in _INTENT_MAP:
        if tag in cleaned:
            art = _INTENT_MAP[tag]
            return {"answer": art.answer, "followups": " | ".join(art.followups), "source": art.id}

    # Keyword scoring (optionally bias by role)
    scores: Dict[str, int] = {}
    words = _WORD_RE.findall(cleaned)
    for w in words:
        for art in _KEYWORD_MAP.get(w, []):
            scores[art.id] = scores.get(art.id, 0) + 1

    # Role bias: add weight if role matches any intent tag of an article
    if role:
        r = role.lower()
        for art in _KB:
            if any(r in tag.lower() for tag in art.intent_tags):
                scores[art.id] = scores.get(art.id, 0) + 2

    if scores:
        best_id = max(scores, key=lambda k: scores[k])
        art = next(a for a in _KB if a.id == best_id)
        return {"answer": art.answer, "followups": " | ".join(art.followups), "source": art.id}

    return {"answer": FALLBACK, "followups": "Try: pricing strategy | compliance matrix | proposal templates", "source": "fallback"}

if __name__ == "__main__":
    # Quick manual test
    tests = [
        "How do I build a technical approach?",
        "past performance references formatting",
        "use pricing calculator margin guidance",
        "create compliance matrix page numbers",
        "where do I find proposal templates",
        "WIN50 discount pricing",
    ]
    for t in tests:
        print(t, "->", get_kb_answer(t)["source"])

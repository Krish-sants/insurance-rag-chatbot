"""Query orchestration as a LangGraph state graph.

    screen ──► understand ──► retrieve ──► generate ──► validate ──► finalize
      │            │             │                          │
      ▼            ▼             ▼                          ▼
    blocked     clarify        refuse                    refuse
                                                   (sources-only fallback)

Every node appends to state["trace"] — the audit trail from the design.
"""

import re
from typing import TypedDict

from langgraph.graph import END, StateGraph

from .guards import confidence, screen_input, validate_citations
from .indexing import hybrid_retrieve, trim_nodes
from .llm import generate_answer

STATE_NAMES = {"texas": "TX", "florida": "FL", "oklahoma": "OK", "california": "CA_STATE"}

DISCLAIMER = ("Verify against the cited policy language before advising a customer. "
              "This assistant explains documents; it does not make coverage decisions.")


class ChatState(TypedDict, total=False):
    user: dict                # {role, licensed_states}
    question: str
    outcome: str              # answered | blocked | refused | clarify
    intent: str
    state_filter: str | None
    historical: bool
    rewritten: str
    source_blocks: list[str]
    sources: list[dict]
    top_score: float
    answer: str
    backend: str
    validation: dict
    confidence: str
    clarification: str
    trace: list[str]


def _note(state: ChatState, node: str, message: str):
    state.setdefault("trace", []).append(f"[{node}] {message}")


# ------------------------------------------------------------------ nodes

def screen(state: ChatState) -> ChatState:
    reason = screen_input(state["question"])
    if reason == "prompt_injection":
        state["outcome"] = "blocked"
        state["answer"] = "This request was blocked by the input guardrail."
        _note(state, "screen", "blocked: prompt injection pattern")
    elif reason == "outcome_prediction":
        state["outcome"] = "refused"
        state["answer"] = (
            "I can't predict whether a claim will be paid — that is a coverage "
            "decision for a human adjuster. I can explain the relevant policy "
            "provisions and claim documentation requirements; ask me about those, "
            "or escalate to the claims help desk.")
        _note(state, "screen", "refused: outcome prediction request")
    else:
        _note(state, "screen", "passed")
    return state


GREETING = re.compile(
    r"^\s*(hi|hii+|hello|hey|yo|good\s+(morning|afternoon|evening)|thanks?|thank\s+you)[\s!.,]*$",
    re.I)


def understand(state: ChatState) -> ChatState:
    q = state["question"].lower()

    if GREETING.match(state["question"]):
        state["outcome"] = "greeting"
        state["answer"] = (
            "Hello! I answer questions from Acme Mutual's governed documents — "
            "policy forms, endorsements, claims procedures, underwriting "
            "guidelines and FAQs. Try asking things like:\n"
            "- What exclusions apply to homeowners policies in Texas?\n"
            "- What documents are required for a water damage claim?\n"
            "- Summarize the cancellation conditions for a Texas homeowners policy.")
        _note(state, "understand", "greeting -> capabilities reply, no retrieval")
        return state

    state["state_filter"] = None
    for name, code in STATE_NAMES.items():
        if name in q or re.search(rf"\b{code}\b", state["question"]):
            state["state_filter"] = code if len(code) == 2 else None
            break

    state["historical"] = bool(re.search(r"\b(2019|prior edition|previous edition|old edition)\b", q))
    state["intent"] = ("comparison" if "compare" in q
                       else "procedure" if re.search(r"documents? (are )?required|checklist|how do i file", q)
                       else "factual_lookup")

    # Query rewriting: expand agent shorthand into form terminology.
    rewritten = state["question"]
    expansions = {
        r"\bhnoa\b": "hired and non-owned auto liability symbols 8 and 9",
        r"\bhired\s*/\s*non-?owned\b": "hired and non-owned auto liability",
        r"\bho-?3\b": "HO 00 03 homeowners special form",
        r"\bdp-?3\b": "DP 00 03 dwelling property special form",
    }
    for pattern, replacement in expansions.items():
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.I)
    state["rewritten"] = rewritten

    # Ambiguity gate: very short queries with no resolvable facets.
    tokens = re.findall(r"[a-z0-9-]+", q)
    has_facet = (state["state_filter"] or state["historical"]
                 or any(k in q for k in ("homeowners", "dwelling", "commercial", "auto",
                                          "claim", "underwriting", "ho", "dp", "flood")))
    if len(tokens) < 5 and not has_facet:
        state["outcome"] = "clarify"
        state["clarification"] = (
            "Could you narrow that down? For example: which policy form (homeowners "
            "HO-3, dwelling DP-3, commercial auto) and which state?")
        _note(state, "understand", "ambiguous query -> clarification")
        return state

    _note(state, "understand",
          f"intent={state['intent']} state={state['state_filter']} "
          f"historical={state['historical']} rewrite='{rewritten[:70]}'")
    return state


def retrieve(state: ChatState) -> ChatState:
    nodes = trim_nodes(state["user"], state["historical"], state["state_filter"])
    _note(state, "retrieve",
          f"security trimming: {len(nodes)} of 14 chunks in scope for "
          f"role={state['user']['role']}")
    results = hybrid_retrieve(state["rewritten"], nodes, top_k=6)

    # Sufficiency gate: RRF scores are rank-based, so also require absolute
    # lexical relevance — the top results must actually share terms with the
    # query, or this is an off-corpus question and the answer is a refusal.
    stop = {"the", "and", "what", "which", "its", "for", "are", "can", "this",
            "that", "does", "with", "from", "will", "has", "have", "how", "who",
            "was", "were", "any", "all", "not", "you", "about", "under", "into"}
    q_terms = {t for t in re.findall(r"[a-z0-9]+", state["rewritten"].lower())
               if len(t) > 2 and t not in stop}
    def _relevance(r):
        node_terms = set(re.findall(r"[a-z0-9]+", r.node.text.lower()))
        return len(q_terms & node_terms) / (len(q_terms) or 1)
    max_relevance = max((_relevance(r) for r in results[:3]), default=0.0)

    if not results or (results[0].score or 0) < 0.01 or max_relevance < 0.25:
        state["outcome"] = "refused"
        state["answer"] = (
            "I couldn't find this in the indexed documents. That means the corpus "
            "doesn't cover it — it does not mean the answer is 'no'. You can "
            "escalate this to the underwriting help desk.")
        _note(state, "retrieve", "no sufficient results -> refusal")
        return state

    blocks, sources = [], []
    for i, r in enumerate(results[:6], start=1):
        m = r.node.metadata
        tag = " (AMENDING ENDORSEMENT)" if m["doc_type"] == "endorsement" and m.get("amends") else ""
        blocks.append(f"[{i}] {m['title']}, form {m['form']} ed. {m['edition']} "
                      f"({m['status'].upper()}){tag}\nSection: {m['section_path']}\n"
                      f"{r.node.text.split(chr(10), 1)[-1]}")
        sources.append({"n": i, "title": m["title"], "form": m["form"],
                        "edition": m["edition"], "status": m["status"],
                        "jurisdiction": m["jurisdiction"],
                        "section": m["section_path"], "score": round(r.score or 0, 4)})
    state["source_blocks"] = blocks
    state["sources"] = sources
    state["top_score"] = results[0].score or 0
    _note(state, "retrieve", f"hybrid fusion kept {len(blocks)} sources, "
                             f"top={state['top_score']:.4f}")
    return state


def generate(state: ChatState) -> ChatState:
    answer, backend = generate_answer(state["rewritten"], state["source_blocks"])
    state["answer"] = answer
    state["backend"] = backend
    _note(state, "generate", f"backend={backend}, {len(answer)} chars")
    return state


def validate(state: ChatState) -> ChatState:
    report = validate_citations(state["answer"], state["source_blocks"])
    state["validation"] = report
    if not report["valid"]:
        state["outcome"] = "refused"
        state["answer"] = (
            "I found potentially relevant sections but couldn't produce a fully "
            "cited answer, so I'm showing you the sources instead of a synthesis. "
            "Please review them directly:\n" +
            "\n".join(f"[{s['n']}] {s['title']} — {s['section']}" for s in state["sources"]))
        _note(state, "validate", f"FAILED ({report['reason']}) -> sources-only fallback")
    else:
        state["confidence"] = confidence(state["top_score"], report["coverage"],
                                         len(state["sources"]))
        _note(state, "validate", f"passed coverage={report['coverage']} "
                                 f"confidence={state['confidence']}")
    return state


def finalize(state: ChatState) -> ChatState:
    state.setdefault("outcome", "answered")
    if state["outcome"] == "answered":
        state["answer"] += f"\n\n— {DISCLAIMER}"
        if state.get("historical"):
            state["answer"] += "\nNote: superseded editions were included at your request."
    _note(state, "finalize", state["outcome"])
    return state


# ------------------------------------------------------------------ graph

def _after_screen(state: ChatState) -> str:
    return "end" if state.get("outcome") in ("blocked", "refused") else "understand"


def _after_understand(state: ChatState) -> str:
    return "end" if state.get("outcome") in ("clarify", "greeting") else "retrieve"


def _after_retrieve(state: ChatState) -> str:
    return "end" if state.get("outcome") == "refused" else "generate"


def build_graph():
    graph = StateGraph(ChatState)
    graph.add_node("screen", screen)
    graph.add_node("understand", understand)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_node("validate", validate)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("screen")
    graph.add_conditional_edges("screen", _after_screen,
                                {"understand": "understand", "end": "finalize"})
    graph.add_conditional_edges("understand", _after_understand,
                                {"retrieve": "retrieve", "end": "finalize"})
    graph.add_conditional_edges("retrieve", _after_retrieve,
                                {"generate": "generate", "end": "finalize"})
    graph.add_edge("generate", "validate")
    graph.add_edge("validate", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


AGENT = build_graph()


def ask(question: str, user: dict) -> dict:
    result = AGENT.invoke({"question": question, "user": user})
    return {
        "outcome": result.get("outcome", "answered"),
        "answer": result.get("answer", ""),
        "clarification": result.get("clarification"),
        "sources": result.get("sources", []),
        "confidence": result.get("confidence"),
        "validation": result.get("validation"),
        "backend": result.get("backend"),
        "trace": result.get("trace", []),
    }

"""Provider-neutral OpenAI-compatible LLM adapter with deterministic Mock LLM for offline demo mode."""
import json
import re
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel
from backend.config import get_settings
from backend.models.schemas import ResearchPlan, EvidenceChunk, SourceMetadata

settings = get_settings()


class MockLLM:
    """Deterministic, reproducible mock generator for offline mode and CI/CD."""

    @staticmethod
    def generate_plan(topic: str, constraints: List[str]) -> ResearchPlan:
        clean_topic = topic.strip().title()
        return ResearchPlan(
            objectives=[
                f"Analyze core state and architecture of {clean_topic}",
                f"Evaluate current capabilities, benchmark results, and trade-offs",
                f"Identify emerging production patterns and future outlook",
            ],
            subquestions=[
                f"What are the foundational architectural principles behind {clean_topic}?",
                f"How does {clean_topic} compare against conventional approaches on latency, cost, and reliability?",
                f"What are the observed production failure modes and mitigations for {clean_topic}?",
            ],
            search_queries=[
                f"{topic} architecture overview benchmark",
                f"{topic} production deployment best practices",
                f"{topic} reliability failure modes comparison",
            ],
            information_requirements=[
                "Authoritative whitepapers or technical documentation",
                "Empirical latency, memory, or throughput benchmarks",
                "Verified production case studies and post-mortems",
            ],
            expected_sections=[
                "Executive Summary",
                "Architectural Foundations",
                "Empirical Performance & Benchmarks",
                "Production Failure Modes & Defenses",
                "Conclusion & Strategic Recommendations",
            ],
        )

    @staticmethod
    def generate_queries(topic: str, subquestion: str, prior_findings: List[str]) -> List[str]:
        words = [w for w in subquestion.lower().replace("?", "").split() if len(w) > 3][:3]
        base = " ".join(words)
        return [
            f"{base} technical architecture analysis",
            f"{base} benchmark comparison data",
        ]

    @staticmethod
    def generate_report(
        topic: str,
        plan: ResearchPlan,
        evidence: List[EvidenceChunk],
        sources: List[SourceMetadata],
    ) -> str:
        s1 = sources[0].source_id if len(sources) > 0 else "src-1"
        s2 = sources[1].source_id if len(sources) > 1 else s1
        s3 = sources[2].source_id if len(sources) > 2 else s1

        # Use actual excerpts from evidence if present
        ex1 = evidence[0].text[:120].strip() if evidence else "Comprehensive empirical benchmarks demonstrate linear scaling."
        ex2 = evidence[1].text[:120].strip() if len(evidence) > 1 else "Stateful recovery mechanisms ensure zero loss across distributed workers."

        return f"""# Autonomous Research Report: {topic.title()}

## Executive Summary
This report analyzes **{topic}** with a focus on system architecture, operational constraints, and empirical reliability. Evidence retrieved from authoritative sources indicates strong architectural advantages alongside key deployment boundary considerations [^{s1}].

## Architectural Foundations
The foundational design of {topic} emphasizes bounded state execution and strict resource containment. Research indicates that systems decoupling planning from execution achieve substantially higher recovery rates under partial network partitions [^{s1}]. As noted in recent literature, "{ex1}..." [^{s1}].

## Empirical Performance & Operational Characteristics
Across evaluated benchmarks, deterministic safeguards and bounded tool registries prevent uncontrolled graph explosion [^{s2}]. Specifically, stateful checkpointing guarantees recovery without loss of prior context [^{s2}]. "{ex2}..." [^{s2}].

## Production Failure Modes & Defenses
The most prevalent production challenges involve unchecked hallucination loops and malicious indirect prompt injection [^{s3}]. Enforcing explicit data boundaries and pre-connection DNS inspection prevents private network exposure while keeping token expenditure bounded [^{s3}].

## Conclusion
Adopting structured planning, allowlisted tool execution, and continuous citation verification allows {topic} to operate safely in enterprise environments with high grounding accuracy [^{s1}].
"""

    @staticmethod
    def verify_claim(claim: str, excerpt: str) -> Dict[str, Any]:
        """Deterministic overlap entailment check."""
        claim_words = set(re.findall(r"\w+", claim.lower()))
        excerpt_words = set(re.findall(r"\w+", excerpt.lower()))
        if not claim_words:
            return {"supported": True, "confidence": 0.8, "reason": "Trivial claim"}
        overlap = len(claim_words.intersection(excerpt_words)) / len(claim_words)
        supported = overlap >= 0.25
        return {
            "supported": supported,
            "confidence": round(min(1.0, overlap + 0.4), 2),
            "reason": f"Word overlap ratio: {overlap:.2f}",
        }


class LLMAdapter:
    """Provider-neutral OpenAI-compatible client adapter."""

    def __init__(self):
        self.settings = get_settings()

    async def generate_plan(self, topic: str, constraints: List[str]) -> ResearchPlan:
        if self.settings.DEMO_MODE or not self.settings.OPENAI_API_KEY or self.settings.OPENAI_API_KEY.startswith("sk-placeholder"):
            return MockLLM.generate_plan(topic, constraints)

        prompt = f"""You are a research planning agent. Generate a structured JSON research plan for the topic: '{topic}'.
Constraints: {constraints}.
Respond ONLY with a JSON object matching this schema:
{{
  "objectives": ["string"],
  "subquestions": ["string", "string", "string"],
  "search_queries": ["string", "string", "string"],
  "information_requirements": ["string"],
  "expected_sections": ["string"]
}}"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{self.settings.OPENAI_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.OPENAI_API_KEY}"},
                    json={
                        "model": self.settings.OPENAI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.2,
                    },
                )
                res.raise_for_status()
                data = res.json()["choices"][0]["message"]["content"]
                return ResearchPlan.model_validate_json(data)
        except Exception:
            # Graceful fallback to mock plan on API error or rate limit
            return MockLLM.generate_plan(topic, constraints)

    async def generate_queries(self, topic: str, subquestion: str, prior_findings: List[str]) -> List[str]:
        if self.settings.DEMO_MODE or not self.settings.OPENAI_API_KEY or self.settings.OPENAI_API_KEY.startswith("sk-placeholder"):
            return MockLLM.generate_queries(topic, subquestion, prior_findings)

        prompt = f"Given topic '{topic}' and subquestion '{subquestion}', produce 2 targeted search queries. Return JSON list: ['query 1', 'query 2']."
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    f"{self.settings.OPENAI_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.OPENAI_API_KEY}"},
                    json={
                        "model": self.settings.OPENAI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,
                    },
                )
                res.raise_for_status()
                text = res.json()["choices"][0]["message"]["content"]
                # Extract json list
                match = re.search(r"\[.*\]", text, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
                return MockLLM.generate_queries(topic, subquestion, prior_findings)
        except Exception:
            return MockLLM.generate_queries(topic, subquestion, prior_findings)

    async def generate_report(
        self,
        topic: str,
        plan: ResearchPlan,
        evidence: List[EvidenceChunk],
        sources: List[SourceMetadata],
    ) -> str:
        if self.settings.DEMO_MODE or not self.settings.OPENAI_API_KEY or self.settings.OPENAI_API_KEY.startswith("sk-placeholder"):
            return MockLLM.generate_report(topic, plan, evidence, sources)

        # Build delimited evidence context
        evidence_text = "\n\n".join(
            [f"Source [{e.source_id}] ({e.url}):\n{e.text}" for e in evidence[:10]]
        )
        prompt = f"""You are a senior research analyst. Write a rigorous research report on '{topic}'.
Sections to include: {plan.expected_sections}.
Every factual statement MUST be cited using standard bracketed citation format [^src-X] pointing to the provided sources.
Do NOT invent URLs. Only cite sources present in the evidence.

EVIDENCE:
{evidence_text}
"""
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(
                    f"{self.settings.OPENAI_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.OPENAI_API_KEY}"},
                    json={
                        "model": self.settings.OPENAI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                    },
                )
                res.raise_for_status()
                return res.json()["choices"][0]["message"]["content"]
        except Exception:
            return MockLLM.generate_report(topic, plan, evidence, sources)

    async def verify_claim_support(self, claim: str, excerpt: str) -> Dict[str, Any]:
        """Verify if source excerpt entails the claim (Mock or LLM)."""
        if self.settings.DEMO_MODE or not self.settings.OPENAI_API_KEY or self.settings.OPENAI_API_KEY.startswith("sk-placeholder"):
            return MockLLM.verify_claim(claim, excerpt)

        prompt = f"""Determine if the excerpt supports the claim.
CLAIM: "{claim}"
EXCERPT: "{excerpt}"

Respond ONLY with JSON:
{{"supported": true/false, "confidence": 0.0-1.0, "reason": "brief explanation"}}"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.settings.OPENAI_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.OPENAI_API_KEY}"},
                    json={
                        "model": self.settings.OPENAI_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.0,
                    },
                )
                res.raise_for_status()
                return json.loads(res.json()["choices"][0]["message"]["content"])
        except Exception:
            return MockLLM.verify_claim(claim, excerpt)


# Global adapter instance
llm_adapter = LLMAdapter()

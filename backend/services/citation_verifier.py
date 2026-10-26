"""Dual-stage citation verification engine: deterministic syntax check + semantic grounding."""
import re
from typing import Dict, List, Tuple, Any
from backend.models.schemas import (
    CitationStatus,
    CitationVerificationResult,
    SourceMetadata,
    EvidenceChunk,
)
from backend.services.llm_adapter import llm_adapter


CITATION_REGEX = re.compile(r"\[\^(src-\d+)\]")


async def verify_citations(
    draft_markdown: str,
    sources: Dict[str, Dict[str, Any]],
    evidence: List[Dict[str, Any]],
) -> Tuple[List[CitationVerificationResult], str, float]:
    """
    Verify all citations in the draft markdown report:
    1. Deterministic check: ensure every [^src-X] maps to a registered source in `sources`.
    2. Grounding check: verify that the sentence asserting the citation is entailed by the source's evidence.
    3. Replaces unsupported claims with explicit uncertainty qualifiers if necessary.
    4. Appends a verified citation matrix table to the report.
    Returns (results, audited_markdown, grounding_score).
    """
    if not draft_markdown:
        return [], "", 0.0

    # Find all citation occurrences and their enclosing sentences
    # Split draft into sentences
    sentences = re.split(r"(?<=[.!?])\s+", draft_markdown)
    citation_results: List[CitationVerificationResult] = []

    # Map source_id to concatenated evidence text
    source_evidence_map: Dict[str, List[str]] = {}
    for ch in evidence:
        s_id = ch.get("source_id", "")
        if s_id not in source_evidence_map:
            source_evidence_map[s_id] = []
        source_evidence_map[s_id].append(ch.get("text", ""))

    audited_sentences = []

    for sentence in sentences:
        citations_found = CITATION_REGEX.findall(sentence)
        if not citations_found:
            audited_sentences.append(sentence)
            continue

        sentence_verified = True
        modified_sentence = sentence

        for src_id in citations_found:
            marker = f"[^{src_id}]"

            # Check 1: Existence in source registry
            if src_id not in sources:
                res = CitationVerificationResult(
                    citation_marker=marker,
                    source_id=src_id,
                    url=None,
                    claimed_statement=sentence.strip(),
                    supporting_excerpt=None,
                    status=CitationStatus.HALLUCINATED_ID,
                    confidence=0.0,
                    note="Citation ID not found in retrieved sources registry",
                )
                citation_results.append(res)
                # Remove hallucinated marker from sentence
                modified_sentence = modified_sentence.replace(marker, "[Citation Unresolved]")
                sentence_verified = False
                continue

            source_meta = sources[src_id]
            src_url = source_meta.get("url")
            available_excerpts = source_evidence_map.get(src_id, [])
            combined_excerpt = " ".join(available_excerpts)

            # Check 2: Excerpt support entailment
            clean_claim = re.sub(r"\[\^src-\d+\]", "", sentence).strip()
            entailment = await llm_adapter.verify_claim_support(clean_claim, combined_excerpt)

            is_supported = entailment.get("supported", False)
            confidence = float(entailment.get("confidence", 0.5))

            best_excerpt = None
            if available_excerpts:
                # Find excerpt with highest token overlap
                claim_tokens = set(re.findall(r"\w+", clean_claim.lower()))
                scored = []
                for ex in available_excerpts:
                    ex_tokens = set(re.findall(r"\w+", ex.lower()))
                    overlap = len(claim_tokens.intersection(ex_tokens))
                    scored.append((overlap, ex))
                scored.sort(key=lambda x: x[0], reverse=True)
                best_excerpt = scored[0][1][:180] + "..." if scored else None

            if is_supported:
                res = CitationVerificationResult(
                    citation_marker=marker,
                    source_id=src_id,
                    url=src_url,
                    claimed_statement=clean_claim,
                    supporting_excerpt=best_excerpt,
                    status=CitationStatus.VERIFIED,
                    confidence=confidence,
                    note=entailment.get("reason", "Directly entailed by source text"),
                )
            else:
                sentence_verified = False
                res = CitationVerificationResult(
                    citation_marker=marker,
                    source_id=src_id,
                    url=src_url,
                    claimed_statement=clean_claim,
                    supporting_excerpt=best_excerpt,
                    status=CitationStatus.UNSUPPORTED,
                    confidence=confidence,
                    note=entailment.get("reason", "Evidence does not sufficiently support claim"),
                )

            citation_results.append(res)

        # If claim had unsupported citations, qualify it with uncertainty
        if not sentence_verified and "[Citation Unresolved]" not in modified_sentence:
            # We preserve the claim but tag it clearly
            modified_sentence = f"{modified_sentence} *(Note: Empirical evidence is partially inconclusive)*"

        audited_sentences.append(modified_sentence)

    reconstructed_body = " ".join(audited_sentences)

    # Compute grounding score
    total_citations = len(citation_results)
    verified_count = sum(1 for c in citation_results if c.status == CitationStatus.VERIFIED)
    grounding_score = round(verified_count / max(1, total_citations), 3) if total_citations > 0 else 1.0

    # Build Citation Audit Appendix Table
    appendix_rows = []
    appendix_rows.append("\n\n---\n## Verified Sources & Citation Audit Matrix\n")
    appendix_rows.append("| Citation | Source Domain | Verification Status | Confidence | Supporting Excerpt |")
    appendix_rows.append("|:---|:---|:---:|:---:|:---|")

    for c in citation_results:
        src = sources.get(c.source_id, {})
        domain = src.get("domain", "Unknown")
        url = src.get("url", "#")
        excerpt = (c.supporting_excerpt or "No excerpt available").replace("|", "-").replace("\n", " ")
        status_badge = "✅ Verified" if c.status == CitationStatus.VERIFIED else "⚠️ Unsupported"
        appendix_rows.append(
            f"| `{c.citation_marker}` | [{domain}]({url}) | {status_badge} | {c.confidence:.2f} | \"{excerpt}\" |"
        )

    final_report_markdown = reconstructed_body + "\n" + "\n".join(appendix_rows)
    return citation_results, final_report_markdown, grounding_score

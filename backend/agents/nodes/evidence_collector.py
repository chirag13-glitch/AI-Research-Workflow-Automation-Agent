"""Evidence collector node: parses HTML, extracts text, chunks, deduplicates, and maps source IDs."""
from datetime import datetime
import hashlib
from typing import Dict, List, Any
from urllib.parse import urlparse
from backend.agents.state import ResearchAgentState
from backend.tools.content_extractor import extract_html_text, chunk_extracted_text
from backend.models.schemas import TaskStatus


async def evidence_collector_node(state: ResearchAgentState) -> ResearchAgentState:
    """
    Process raw tool results:
    - Extract readable text from fetched HTML
    - Assign stable source IDs (src-1, src-2, ...)
    - Chunk text and deduplicate via SHA-256
    - Link every evidence chunk to its canonical source
    """
    raw_results = state.get("raw_tool_results", [])
    collected_sources: Dict[str, Dict[str, Any]] = dict(state.get("collected_sources", {}))
    evidence_chunks: List[Dict[str, Any]] = list(state.get("evidence_chunks", []))
    existing_chunk_hashes = {
        hashlib.sha256(c["text"].encode("utf-8")).hexdigest() for c in evidence_chunks
    }

    source_counter = len(collected_sources) + 1

    for res in raw_results:
        if res.get("tool") == "fetch_web_page" and "data" in res:
            page_data = res["data"]
            url = page_data.get("url", "")
            html = page_data.get("html", "")
            if not html or not url:
                continue

            # Check if source is already cataloged
            existing_src_id = None
            for s_id, s_meta in collected_sources.items():
                if s_meta.get("url") == url:
                    existing_src_id = s_id
                    break

            if not existing_src_id:
                src_id = f"src-{source_counter}"
                source_counter += 1
                extracted = extract_html_text(html, url)
                title = extracted.get("title") or urlparse(url).netloc
                domain = extracted.get("domain") or urlparse(url).netloc
                full_text = extracted.get("text", "")

                collected_sources[src_id] = {
                    "source_id": src_id,
                    "url": url,
                    "title": title,
                    "domain": domain,
                    "retrieved_at": datetime.utcnow().isoformat(),
                    "status_code": page_data.get("status_code", 200),
                    "is_trusted": not extracted.get("has_injection", False),
                }

                # Chunk and store evidence
                chunks = chunk_extracted_text(full_text)
                for i, ch_text in enumerate(chunks):
                    ch_hash = hashlib.sha256(ch_text.encode("utf-8")).hexdigest()
                    if ch_hash not in existing_chunk_hashes:
                        existing_chunk_hashes.add(ch_hash)
                        evidence_chunks.append({
                            "chunk_id": f"{src_id}_chk_{i+1}",
                            "source_id": src_id,
                            "url": url,
                            "text": ch_text,
                            "char_count": len(ch_text),
                        })

    log_entry = {
        "node": "evidence_collector",
        "status": "COMPLETED",
        "message": f"Cataloged {len(collected_sources)} sources and {len(evidence_chunks)} unique evidence chunks.",
        "timestamp": datetime.utcnow().isoformat(),
    }

    return {
        **state,
        "status": TaskStatus.COLLECTING_EVIDENCE.value,
        "collected_sources": collected_sources,
        "evidence_chunks": evidence_chunks,
        "step_history": [*state.get("step_history", []), log_entry],
    }

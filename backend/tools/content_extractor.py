"""HTML text extraction, metadata parsing, and semantic chunking."""
import hashlib
import re
from typing import Dict, List, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from backend.services.content_sanitizer import sanitize_text_content


def extract_html_text(html_content: str, url: str) -> Dict[str, Any]:
    """
    Parse HTML, extract title, clean text, and strip boilerplate/scripts.
    Returns structured article metadata and cleaned text.
    """
    if not html_content:
        return {
            "title": "Untitled",
            "domain": urlparse(url).netloc,
            "text": "",
            "char_count": 0,
            "has_injection": False,
        }

    soup = BeautifulSoup(html_content, "html.parser")

    # Extract title
    title = "Untitled"
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)

    # Remove non-content elements
    for element in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside", "form"]):
        element.decompose()

    # Extract text from paragraphs and headings
    paragraphs = []
    for tag in soup.find_all(["p", "h1", "h2", "h3", "h4", "li"]):
        txt = tag.get_text(separator=" ", strip=True)
        if len(txt) > 20:
            paragraphs.append(txt)

    combined_text = "\n\n".join(paragraphs)
    if not combined_text:
        combined_text = soup.get_text(separator=" ", strip=True)

    sanitized_text, has_injection = sanitize_text_content(combined_text)
    domain = urlparse(url).netloc

    return {
        "title": title[:200],
        "domain": domain,
        "text": sanitized_text,
        "char_count": len(sanitized_text),
        "has_injection": has_injection,
    }


def chunk_extracted_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """Split text into overlapping semantic chunks for evidence attribution."""
    if not text:
        return []

    # Split by paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{p}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = p

    if current_chunk:
        chunks.append(current_chunk)

    # Deduplicate chunks
    unique_chunks = []
    seen_hashes = set()
    for ch in chunks:
        ch_hash = hashlib.sha256(ch.encode("utf-8")).hexdigest()
        if ch_hash not in seen_hashes and len(ch) >= 40:
            seen_hashes.add(ch_hash)
            unique_chunks.append(ch)

    return unique_chunks

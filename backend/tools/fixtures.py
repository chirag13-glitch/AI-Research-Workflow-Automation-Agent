"""Saved fixtures for offline demo mode and deterministic testing."""
from typing import Dict, List, Any

# Curated search fixtures mapping keyword queries to realistic search outputs
SEARCH_FIXTURES: Dict[str, List[Dict[str, str]]] = {
    "default": [
        {
            "url": "https://research.systems-engineering.org/papers/stateful-agents",
            "title": "Stateful Agent Architectures: Checkpointing, Fault Tolerance and Memory Boundedness",
            "snippet": "We present an empirical study on stateful autonomous AI agents. By utilizing bounded graph transitions and persistent transactional checkpointers, agent state survives network partitions and worker restarts with zero token loss. Microbenchmarks reveal a 94.2% recovery rate under partial infrastructure failure.",
        },
        {
            "url": "https://ieee-computer-standards.org/proceedings/evaluating-llm-workflows",
            "title": "Evaluating Bounded Execution Graphs in Production LLM Pipelines",
            "snippet": "Empirical analysis shows that unbound iterative agent loops account for over 68% of unexpected cloud cost overruns. Enforcing hard execution budgets and explicit entailment verification reduces hallucinated citations from 32% down to under 1.5% in multi-hop research tasks.",
        },
        {
            "url": "https://cloud-native-security.io/reports/ssrf-and-prompt-injection-defenses",
            "title": "Comprehensive Threat Analysis of Agentic Retrieval: SSRF, Link-Local Exploits and Indirect Injections",
            "snippet": "Autonomous agents fetching untrusted web pages face acute vulnerabilities to SSRF attacks targeting link-local metadata endpoints (169.254.169.254). Strict pre-connection DNS validation combined with XML data isolation successfully mitigates 100% of tested indirect prompt injection vectors.",
        },
        {
            "url": "https://ai-systems-quarterly.org/benchmarks/autonomous-research-workflows",
            "title": "Autonomous Research Workflows: Multi-Source Synthesis and Citation Verification",
            "snippet": "Evaluating multi-source information synthesis across 1,000 queries demonstrated that two-stage verification (deterministic regex ID check followed by sentence entailment matching) provides 96% citation accuracy compared to human expert ground truth.",
        },
    ]
}

# Pre-saved web page contents
PAGE_FIXTURES: Dict[str, str] = {
    "https://research.systems-engineering.org/papers/stateful-agents": """
    <html>
    <head><title>Stateful Agent Architectures: Checkpointing and Fault Tolerance</title></head>
    <body>
        <h1>Stateful Agent Architectures: Checkpointing, Fault Tolerance and Memory Boundedness</h1>
        <p>In modern autonomous AI architectures, long-running agent workflows must tolerate worker crashes and network disruptions. By adopting transactional checkpointers backed by relational databases like PostgreSQL, agents maintain an immutable log of execution state.</p>
        <p>Our microbenchmarks across 10,000 synthetic runs show a 94.2% recovery rate under simulated worker death. Furthermore, decoupling graph execution from persistence ensures that resumed tasks never re-execute previously verified tool calls, saving an average of 42% in API token expenditure.</p>
        <p>Critical design requirements include: 1) deterministic state machines; 2) human-in-the-loop pause states (AWAITING_APPROVAL) for ambiguous search results; and 3) strict concurrency limits during parallel search execution.</p>
    </body>
    </html>
    """,
    "https://ieee-computer-standards.org/proceedings/evaluating-llm-workflows": """
    <html>
    <head><title>Evaluating Bounded Execution Graphs in Production LLM Pipelines</title></head>
    <body>
        <h1>Evaluating Bounded Execution Graphs in Production LLM Pipelines</h1>
        <p>Iterative agent loops without hard stopping conditions create severe operational liabilities. When research agents encounter sparse or conflicting information on the open web, unconstrained planners frequently initiate runaway query generation cycles.</p>
        <p>In our enterprise survey, runaway cycles accounted for 68% of unexpected token budget overruns. Enforcing a hard budget of 15 tool calls per task eliminated budget spikes while preserving 98% of report quality.</p>
        <p>Furthermore, two-stage citation verification—combining deterministic regex extraction of citation markers with claim entailment checking—lowered the incidence of hallucinated citations from 32% to 1.4%.</p>
    </body>
    </html>
    """,
    "https://cloud-native-security.io/reports/ssrf-and-prompt-injection-defenses": """
    <html>
    <head><title>Threat Analysis of Agentic Retrieval: SSRF and Indirect Injection Defenses</title></head>
    <body>
        <h1>Comprehensive Threat Analysis of Agentic Retrieval</h1>
        <p>When autonomous AI agents are equipped with web-fetching tools, they become vulnerable to Server-Side Request Forgery (SSRF). Attackers frequently host domains that resolve to internal private IP ranges (RFC 1918) or cloud provider link-local metadata endpoints (169.254.169.254).</p>
        <p>To defend against these vectors, production architectures must perform pre-connection DNS address inspection, rejecting all private, loopback, and multicast ranges before initiating HTTP connections. Safe redirect validation is equally essential to prevent open redirects from bypassing initial checks.</p>
        <p>For indirect prompt injection embedded in HTML documents, passive XML boundaries and heuristic regex sanitizers successfully defuse 100% of tested instruction override attempts.</p>
    </body>
    </html>
    """,
    "https://ai-systems-quarterly.org/benchmarks/autonomous-research-workflows": """
    <html>
    <head><title>Autonomous Research Workflows: Multi-Source Synthesis</title></head>
    <body>
        <h1>Autonomous Research Workflows: Multi-Source Synthesis and Verification</h1>
        <p>Synthesizing research reports from disparate web sources requires strict adherence to evidence grounding. High-quality research agents must distinguish between a valid URL and an excerpt that actually supports the generated claim.</p>
        <p>Our benchmark across 1,000 multi-source inquiries demonstrates that dual-stage verification (deterministic source ID validation followed by snippet entailment matching) achieves 96% concordance with human expert evaluation.</p>
        <p>When evidence is insufficient or contradictory, agents must explicitly state uncertainty rather than interpolating speculative claims.</p>
    </body>
    </html>
    """,
}


def get_mock_search_results(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Return realistic mock search results."""
    results = SEARCH_FIXTURES.get("default", [])
    # Return formatted results up to max_results
    return results[:max_results]


def get_mock_page_html(url: str) -> str:
    """Return pre-saved HTML for a given URL or generate a realistic fallback."""
    if url in PAGE_FIXTURES:
        return PAGE_FIXTURES[url]
    # Fallback realistic HTML
    return f"""
    <html>
    <head><title>Technical Reference: {url}</title></head>
    <body>
        <h1>Technical Research Findings for {url}</h1>
        <p>Empirical analysis confirms that stateful architectures and bounded execution provide high reliability and deterministic recovery. All citations must be grounded in verified source excerpts.</p>
        <p>Systems with strict tool allowlists and SSRF guards effectively prevent unauthorized internal network access while maintaining robust retrieval throughput.</p>
    </body>
    </html>
    """

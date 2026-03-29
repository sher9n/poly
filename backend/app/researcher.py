"""Research engine that gathers info and synthesizes a prediction."""
import httpx
import json
import re
from bs4 import BeautifulSoup
from typing import Optional


async def research_event(question: str, description: str = "", category: str = "other") -> dict:
    """
    Research an event by searching the web and synthesizing findings.
    Returns a dict with:
      - predicted_outcome: "YES" or "NO"
      - confidence: 0.0 to 1.0
      - summary: text explanation
      - sources: list of source descriptions
      - key_factors: list of factors considered
    """
    # Step 1: Break down what we need to analyze
    search_queries = _generate_search_queries(question, category)

    # Step 2: Gather information from multiple sources
    all_findings = []
    sources = []

    for query in search_queries[:3]:  # Limit to 3 searches
        results = await _web_search(query)
        for result in results[:3]:
            finding = await _extract_content(result["url"])
            if finding:
                all_findings.append({
                    "query": query,
                    "title": result.get("title", ""),
                    "url": result["url"],
                    "content": finding[:2000],  # Limit content length
                })
                sources.append(f"{result.get('title', 'Unknown')}: {result['url']}")

    # Step 3: Synthesize findings into a prediction
    # If no web data available, use heuristic analysis
    if not all_findings:
        prediction = _heuristic_analysis(question, description, category)
    else:
        prediction = _synthesize(question, description, all_findings, category)

    return {
        "predicted_outcome": prediction["outcome"],
        "confidence": prediction["confidence"],
        "summary": prediction["summary"],
        "sources": sources if sources else ["Heuristic analysis (web search unavailable)"],
        "key_factors": prediction["key_factors"],
    }


def _generate_search_queries(question: str, category: str) -> list[str]:
    """Generate targeted search queries based on the event question."""
    # Clean up the question for search
    clean_q = question.replace("?", "").strip()

    queries = [
        f"{clean_q} latest news",
        f"{clean_q} prediction analysis",
    ]

    if category == "politics":
        queries.append(f"{clean_q} polls data")
    elif category == "sports":
        queries.append(f"{clean_q} odds statistics")
    elif category == "crypto":
        queries.append(f"{clean_q} price analysis forecast")
    elif category == "finance":
        queries.append(f"{clean_q} market analysis forecast")
    else:
        queries.append(f"{clean_q} likelihood analysis")

    return queries


async def _web_search(query: str) -> list[dict]:
    """Search the web using DuckDuckGo HTML."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            results = []

            for result_div in soup.select(".result__body")[:5]:
                title_el = result_div.select_one(".result__title a")
                snippet_el = result_div.select_one(".result__snippet")

                if title_el:
                    href = title_el.get("href", "")
                    # DuckDuckGo redirects - extract actual URL
                    if "uddg=" in href:
                        from urllib.parse import unquote, urlparse, parse_qs
                        parsed = parse_qs(urlparse(href).query)
                        href = unquote(parsed.get("uddg", [href])[0])

                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": href,
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })

            return results
    except Exception:
        return []


async def _extract_content(url: str) -> Optional[str]:
    """Extract main text content from a URL."""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove script and style elements
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # Get text from article or main content
            article = soup.find("article") or soup.find("main") or soup.find("body")
            if not article:
                return None

            text = article.get_text(separator=" ", strip=True)
            # Clean up whitespace
            text = re.sub(r"\s+", " ", text)
            return text[:3000] if text else None
    except Exception:
        return None


def _synthesize(question: str, description: str, findings: list[dict], category: str) -> dict:
    """
    Analyze findings and produce a prediction.
    Uses keyword/sentiment analysis as a lightweight synthesis approach.
    """
    if not findings:
        return {
            "outcome": "YES",
            "confidence": 0.5,
            "summary": "Insufficient data to make a strong prediction. Defaulting to market consensus.",
            "key_factors": ["No reliable sources found"],
        }

    question_lower = question.lower()
    combined_text = " ".join(f.get("content", "") for f in findings).lower()

    # Analyze sentiment toward YES outcome
    yes_signals = 0
    no_signals = 0
    key_factors = []

    # Positive indicators (supporting YES)
    yes_keywords = ["likely", "expected", "will", "confirmed", "agreed", "approved",
                     "winning", "leading", "ahead", "positive", "strong", "increase",
                     "surge", "rally", "gain", "success", "breakthrough"]
    no_keywords = ["unlikely", "won't", "denied", "rejected", "failed", "losing",
                    "behind", "negative", "weak", "decrease", "drop", "fall",
                    "decline", "setback", "obstacle", "against"]

    for word in yes_keywords:
        count = combined_text.count(word)
        if count > 0:
            yes_signals += count
            if count >= 2:
                key_factors.append(f"Multiple mentions of '{word}' in sources ({count}x)")

    for word in no_keywords:
        count = combined_text.count(word)
        if count > 0:
            no_signals += count
            if count >= 2:
                key_factors.append(f"Multiple mentions of '{word}' in sources ({count}x)")

    # Look for specific data points
    # Percentages
    pct_matches = re.findall(r"(\d{1,3})%", combined_text)
    if pct_matches:
        avg_pct = sum(int(p) for p in pct_matches) / len(pct_matches)
        key_factors.append(f"Average percentage mentioned in sources: {avg_pct:.0f}%")

    # Calculate confidence
    total_signals = yes_signals + no_signals
    if total_signals == 0:
        confidence = 0.5
        outcome = "YES"
    else:
        yes_ratio = yes_signals / total_signals
        if yes_ratio > 0.5:
            outcome = "YES"
            confidence = min(0.55 + (yes_ratio - 0.5) * 0.8, 0.95)
        else:
            outcome = "NO"
            confidence = min(0.55 + (0.5 - yes_ratio) * 0.8, 0.95)

    if not key_factors:
        key_factors = ["General sentiment analysis of available sources"]

    # Build summary
    source_count = len(findings)
    summary_parts = [
        f"Analyzed {source_count} sources for: '{question}'.",
        f"Signal analysis: {yes_signals} positive vs {no_signals} negative indicators.",
        f"Prediction: {outcome} with {confidence:.0%} confidence.",
    ]
    if key_factors:
        summary_parts.append("Key factors: " + "; ".join(key_factors[:5]))

    return {
        "outcome": outcome,
        "confidence": confidence,
        "summary": " ".join(summary_parts),
        "key_factors": key_factors[:5],
    }


def _heuristic_analysis(question: str, description: str, category: str) -> dict:
    """
    Heuristic-based prediction when web search is unavailable.
    Analyzes the question structure and category to make a reasoned prediction.
    """
    import random
    q = question.lower()
    key_factors = []

    # Analyze question framing
    # Questions with "will X exceed/surpass/break" tend to be harder (lower probability)
    if any(w in q for w in ["exceed", "surpass", "break", "above", "over", "more than"]):
        base_confidence = 0.60
        lean = "NO"
        key_factors.append("Question asks about exceeding a threshold - historically less likely")
    elif any(w in q for w in ["will", "does", "can"]):
        base_confidence = 0.58
        lean = "YES"
        key_factors.append("Standard predictive question - slight lean toward status quo")
    else:
        base_confidence = 0.55
        lean = "YES"

    # Category-specific heuristics
    if category == "crypto":
        key_factors.append("Crypto markets: high volatility, dramatic moves possible but threshold-breaking events are rare short-term")
        if "exceed" in q or "above" in q or "flip" in q:
            lean = "NO"
            base_confidence = 0.65
    elif category == "politics":
        if any(w in q for w in ["sign", "announce", "executive order"]):
            lean = "YES"
            base_confidence = 0.70
            key_factors.append("Political action items have high follow-through when anticipated")
        elif "ceasefire" in q or "peace" in q:
            lean = "NO"
            base_confidence = 0.72
            key_factors.append("Diplomatic breakthroughs are rare in short timeframes")
    elif category == "sports":
        if any(w in q for w in ["150", "record", "historic"]):
            lean = "NO"
            base_confidence = 0.68
            key_factors.append("Extreme statistical outcomes are unlikely in any given week")
        elif "distance" in q or "decision" in q:
            lean = "NO"
            base_confidence = 0.60
            key_factors.append("Most high-profile fights end before going the distance")
    elif category == "finance":
        if "rate cut" in q and any(w in q for w in ["this week", "tomorrow"]):
            lean = "NO"
            base_confidence = 0.75
            key_factors.append("Fed rate decisions are well-telegraphed; surprise cuts are very rare")
        elif "close above" in q:
            lean = "YES"
            base_confidence = 0.58
            key_factors.append("Market levels near current prices have ~50/50 chance, slight upward bias")
    elif category == "science":
        if "spacex" in q or "launch" in q:
            lean = "YES"
            base_confidence = 0.62
            key_factors.append("SpaceX has high launch success rate in recent years")

    # Add small random variation to avoid identical predictions
    noise = random.uniform(-0.03, 0.03)
    confidence = min(0.92, max(0.52, base_confidence + noise))

    if not key_factors:
        key_factors = ["Heuristic analysis based on question structure and category"]

    summary = (
        f"Heuristic analysis for: '{question}'. "
        f"Web search unavailable - using question structure and category-based reasoning. "
        f"Prediction: {lean} with {confidence:.0%} confidence. "
        f"Key factors: {'; '.join(key_factors[:3])}"
    )

    return {
        "outcome": lean,
        "confidence": confidence,
        "summary": summary,
        "key_factors": key_factors,
    }

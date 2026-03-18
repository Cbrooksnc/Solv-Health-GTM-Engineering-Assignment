"""
Signal detector — queries SerpAPI for each buying signal.
Each detect_* method returns a SignalResult with score (0-1) and evidence.
"""
import os
import re
import time
from typing import List, Optional

from .base import SignalResult

try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False


def _serp_search(query: str, api_key: str, num: int = 10) -> List[dict]:
    """Execute a SerpAPI Google search and return organic results."""
    if not SERPAPI_AVAILABLE:
        return []
    try:
        params = {
            "q": query,
            "api_key": api_key,
            "num": num,
            "engine": "google",
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        return results.get("organic_results", [])
    except Exception:
        return []


def _snippets(results: List[dict]) -> List[str]:
    return [r.get("snippet", "") for r in results if r.get("snippet")]


def _titles(results: List[dict]) -> List[str]:
    return [r.get("title", "") for r in results if r.get("title")]


def _links(results: List[dict]) -> List[str]:
    return [r.get("link", "") for r in results if r.get("link")]


class SignalDetector:
    """Detects all 7 buying signals for a given company using SerpAPI."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _search(self, query: str, num: int = 10) -> List[dict]:
        results = _serp_search(query, self.api_key, num)
        time.sleep(0.5)  # gentle rate limiting
        return results

    def detect_ehr_migration(self, company: str, region: str) -> SignalResult:
        """EHR go-live or migration announcement — strongest signal, 12-24 month buying window."""
        queries = [
            f'"{company}" EHR migration OR "go-live" OR "new system" urgent care {region}',
            f'"{company}" athenahealth OR Experity OR eClinicalWorks implementation',
        ]
        all_results = []
        for q in queries:
            all_results.extend(self._search(q, 8))

        evidence = []
        score = 0.0
        ehr_keywords = ["ehr", "emr", "migration", "go-live", "golive", "implementation",
                        "new system", "athenahealth", "experity", "eclinicalworks", "ecw",
                        "transition", "rollout", "deploy"]

        for snippet in _snippets(all_results) + _titles(all_results):
            text = snippet.lower()
            matches = sum(1 for kw in ehr_keywords if kw in text)
            if matches >= 2:
                evidence.append(snippet[:200])
                score = min(score + 0.35, 1.0)
            elif matches == 1:
                score = min(score + 0.1, 1.0)

        confidence = "high" if score > 0.6 else "medium" if score > 0.3 else "low"
        return SignalResult(
            signal_name="ehr_migration",
            score=score,
            evidence=evidence[:3],
            confidence=confidence,
            sources=_links(all_results)[:3],
        )

    def detect_leadership_hire(self, company: str, region: str) -> SignalResult:
        """New VP Ops, COO, or Director of Operations in past 90 days."""
        queries = [
            f'"{company}" "new" OR "joins" OR "appointed" "VP Operations" OR "COO" OR "Director of Operations" 2024 OR 2025',
            f'"{company}" site:linkedin.com OR site:businesswire.com OR site:prnewswire.com "joins" operations',
        ]
        all_results = []
        for q in queries:
            all_results.extend(self._search(q, 8))

        evidence = []
        score = 0.0
        hire_keywords = ["appointed", "joins", "named", "hired", "new coo", "new vp",
                         "director of operations", "chief operating", "vp of operations",
                         "vp operations", "joins as"]

        for snippet in _snippets(all_results) + _titles(all_results):
            text = snippet.lower()
            if any(kw in text for kw in hire_keywords):
                evidence.append(snippet[:200])
                score = min(score + 0.45, 1.0)

        confidence = "high" if score > 0.6 else "medium" if score > 0.3 else "low"
        return SignalResult(
            signal_name="leadership_hire",
            score=score,
            evidence=evidence[:3],
            confidence=confidence,
            sources=_links(all_results)[:3],
        )

    def detect_ma_activity(self, company: str, region: str) -> SignalResult:
        """PE acquisition, M&A, or roll-up activity."""
        queries = [
            f'"{company}" acquisition OR "acquired by" OR "private equity" OR "PE firm" urgent care',
            f'"{company}" merger OR "roll-up" OR "portfolio" OR "backed by"',
        ]
        all_results = []
        for q in queries:
            all_results.extend(self._search(q, 8))

        evidence = []
        score = 0.0
        ma_keywords = ["acquired", "acquisition", "private equity", "merger", "roll-up",
                       "portfolio company", "backed by", "investment", "pe firm", "capital partners"]

        for snippet in _snippets(all_results) + _titles(all_results):
            text = snippet.lower()
            if any(kw in text for kw in ma_keywords):
                evidence.append(snippet[:200])
                score = min(score + 0.4, 1.0)

        confidence = "high" if score > 0.6 else "medium" if score > 0.3 else "low"
        return SignalResult(
            signal_name="ma_activity",
            score=score,
            evidence=evidence[:3],
            confidence=confidence,
            sources=_links(all_results)[:3],
        )

    def detect_job_postings(self, company: str, region: str) -> SignalResult:
        """High volume of front-desk and receptionist postings, especially 'urgently hiring'."""
        queries = [
            f'"{company}" "front desk" OR "receptionist" OR "patient registration" site:indeed.com OR site:linkedin.com OR site:glassdoor.com',
            f'"{company}" "urgently hiring" OR "immediate opening" front desk medical',
        ]
        all_results = []
        for q in queries:
            all_results.extend(self._search(q, 10))

        evidence = []
        score = 0.0
        job_keywords = ["front desk", "receptionist", "patient registration", "check-in",
                        "urgent", "immediately", "opening", "hiring", "apply now"]

        count = 0
        for snippet in _snippets(all_results) + _titles(all_results):
            text = snippet.lower()
            matches = sum(1 for kw in job_keywords if kw in text)
            if matches >= 2:
                evidence.append(snippet[:200])
                count += 1
                score = min(score + 0.3, 1.0)
            elif matches == 1:
                count += 1
                score = min(score + 0.1, 1.0)

        # More postings = stronger signal
        if count >= 5:
            score = min(score + 0.2, 1.0)

        confidence = "high" if score > 0.6 else "medium" if score > 0.3 else "low"
        return SignalResult(
            signal_name="job_postings",
            score=score,
            evidence=evidence[:3],
            confidence=confidence,
            sources=_links(all_results)[:3],
        )

    def detect_patient_reviews(self, company: str, region: str) -> SignalResult:
        """Reviews citing hold times, no answer, check-in delays, system issues."""
        queries = [
            f'"{company}" reviews "on hold" OR "wait time" OR "couldn\'t get through" OR "check in" urgent care',
            f'"{company}" site:google.com OR site:yelp.com "phone" OR "hold" OR "wait" OR "system" complaints',
        ]
        all_results = []
        for q in queries:
            all_results.extend(self._search(q, 10))

        evidence = []
        score = 0.0
        review_keywords = ["hold time", "on hold", "wait time", "couldn't get through",
                           "no answer", "check-in", "check in", "system down", "slow system",
                           "long wait", "understaffed", "overwhelmed", "busy signal"]

        for snippet in _snippets(all_results) + _titles(all_results):
            text = snippet.lower()
            matches = sum(1 for kw in review_keywords if kw in text)
            if matches >= 2:
                evidence.append(snippet[:200])
                score = min(score + 0.35, 1.0)
            elif matches == 1:
                score = min(score + 0.1, 1.0)

        confidence = "high" if score > 0.6 else "medium" if score > 0.3 else "low"
        return SignalResult(
            signal_name="patient_reviews",
            score=score,
            evidence=evidence[:3],
            confidence=confidence,
            sources=_links(all_results)[:3],
        )

    def detect_expansion_news(self, company: str, region: str) -> SignalResult:
        """New location openings, franchise expansion."""
        queries = [
            f'"{company}" "new location" OR "opens" OR "expanding" OR "new clinic" urgent care {region}',
        ]
        all_results = []
        for q in queries:
            all_results.extend(self._search(q, 8))

        evidence = []
        score = 0.0
        expand_keywords = ["new location", "opens", "grand opening", "expanding",
                           "new clinic", "new facility", "additional location", "new market"]

        for snippet in _snippets(all_results) + _titles(all_results):
            text = snippet.lower()
            if any(kw in text for kw in expand_keywords):
                evidence.append(snippet[:200])
                score = min(score + 0.4, 1.0)

        confidence = "high" if score > 0.6 else "medium" if score > 0.3 else "low"
        return SignalResult(
            signal_name="expansion_news",
            score=score,
            evidence=evidence[:3],
            confidence=confidence,
            sources=_links(all_results)[:3],
        )

    def detect_ehr_confirmation(self, company: str, region: str) -> SignalResult:
        """Confirms athenahealth, Experity, or eClinicalWorks — ICP gate, bonus if confirmed."""
        queries = [
            f'"{company}" athenahealth OR Experity OR eClinicalWorks OR "Practice Fusion" EHR urgent care',
            f'"{company}" "powered by" OR "uses" OR "runs on" EMR OR EHR',
        ]
        all_results = []
        for q in queries:
            all_results.extend(self._search(q, 8))

        evidence = []
        score = 0.0
        detected_ehr = None

        icp_map = {
            "athenahealth": "athenahealth",
            "athena": "athenahealth",
            "experity": "Experity",
            "eclinicalworks": "eClinicalWorks",
            "ecw": "eClinicalWorks",
        }

        for snippet in _snippets(all_results) + _titles(all_results):
            text = snippet.lower()
            for kw, ehr_name in icp_map.items():
                if kw in text:
                    evidence.append(snippet[:200])
                    score = 1.0
                    detected_ehr = ehr_name
                    break

        confidence = "high" if score > 0.0 else "low"
        return SignalResult(
            signal_name="ehr_confirmation",
            score=score,
            evidence=evidence[:3],
            confidence=confidence,
            sources=_links(all_results)[:3],
            detected_ehr=detected_ehr,
        )

    def detect_all(self, company: str, region: str) -> dict:
        """Run all signal detectors and return a dict of SignalResult by signal name."""
        detectors = {
            "ehr_migration": self.detect_ehr_migration,
            "leadership_hire": self.detect_leadership_hire,
            "ma_activity": self.detect_ma_activity,
            "job_postings": self.detect_job_postings,
            "patient_reviews": self.detect_patient_reviews,
            "expansion_news": self.detect_expansion_news,
            "ehr_confirmation": self.detect_ehr_confirmation,
        }
        results = {}
        for name, fn in detectors.items():
            results[name] = fn(company, region)
        return results

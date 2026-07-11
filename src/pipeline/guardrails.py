from __future__ import annotations

"""
RAG Query Pipeline — Guardrails & Compliance Module

Detects and filters queries before they reach the main RAG pipeline:
  1. PII detection (PAN, Aadhaar, Phone, Email, OTP)
  2. Advisory query detection (keywords and investment advice patterns)
  3. Off-topic detection (relevance check against HDFC mutual funds scope)
  4. Inappropriate language / Profanity filtering
"""

import re


class Guardrails:
    """Implements safety checks and compliance filters for user queries."""

    # PII Regex Patterns
    # Indian PAN: 5 letters, 4 digits, 1 letter
    PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
    # Indian Aadhaar: 12 digits, optional spaces/hyphens
    AADHAAR_PATTERN = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
    # Indian Phone (10 digits starting with 6-9, optional country code +91 or 91)
    PHONE_PATTERN = re.compile(r"\b(?:\+91|91)?[6-9]\d{9}\b|\b\d{10}\b")
    # Email
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    # OTP
    OTP_PATTERN = re.compile(
        r"\b(?:otp|one[- ]time[- ]password|passcode)\b.*\b\d{4,6}\b|\b\d{4,6}\b.*\b(?:otp|one[- ]time[- ]password|passcode)\b",
        re.IGNORECASE,
    )

    # Advisory Keywords & Phrases
    ADVISORY_PHRASES = [
        "should i invest",
        "should i buy",
        "should i sell",
        "which fund is better",
        "which fund is best",
        "give advice",
        "recommend me",
        "suggest a fund",
        "better return",
        "is it safe",
        "is this fund safe",
        "worth investing",
        "financial advice",
        "which fund is good",
        "best mutual fund",
        "which mutual fund",
        "help me choose",
    ]

    # Inappropriate Language / Profanity list
    PROFANITY_WORDS = [
        "fuck", "shit", "bastard", "idiot", "stupid", "asshole", "bitch", "crap"
    ]

    # On-topic Keyword set (to detect off-topic queries)
    ON_TOPIC_KEYWORDS = {
        "fund", "sip", "nav", "aum", "hdfc", "expense", "load", "lock-in", "lockin",
        "benchmark", "riskometer", "manager", "tax", "holding", "investment", "return",
        "returns", "dividend", "growth", "lumpsum", "equity", "debt", "elss", "mid-cap",
        "midcap", "large-cap", "largecap", "focused", "groww", "statement", "capital gain",
        "gains", "amc", "mutual", "portfolio", "ratio", "download", "exit", "charge",
        "fee", "cost", "how to", "process", "step", "guide", "invest", "buy", "sell",
        "redeem", "redemption", "account", "pan", "aadhaar", "document", "report"
    }

    # Unsupported / Other AMCs to block
    UNSUPPORTED_AMCS = {
        "icici", "sbi", "axis", "nippon", "uti", "tata", "mirae", "kotak", "quant",
        "aditya", "birla", "dsp", "hsbc", "franklin", "motilal", "bandhan", "canara",
        "robeco", "ppfas", "parag", "parikh"
    }

    def check_query(self, query: str) -> dict | None:
        """Run all guardrail checks against the query.

        Args:
            query: User's question.

        Returns:
            Refusal dictionary if a guardrail triggers, or None if the query passes.
        """
        cleaned_query = query.strip()

        # 1. Profanity check (do this first to catch rude messages)
        if self._contains_profanity(cleaned_query):
            return {
                "status": "refused",
                "type": "profanity",
                "answer": "I cannot respond to inappropriate language. Please keep your questions respectful and professional.",
                "citation": None,
                "educational_link": None,
                "footer": "Facts-only. No investment advice.",
            }

        # 2. PII Detection (Sensitive information check)
        if self._contains_pii(cleaned_query):
            # As per requirements, blocked PII queries should never be logged or processed further
            return {
                "status": "refused",
                "type": "pii",
                "answer": "I cannot process queries containing personally identifiable information (PII) such as PAN, Aadhaar, phone numbers, or email addresses. Please remove any sensitive information and try again.",
                "citation": None,
                "educational_link": None,
                "footer": "Facts-only. No investment advice.",
            }

        # 3. Advisory Check (Blocks requests for advice/recommendations)
        if self._is_advisory(cleaned_query):
            return {
                "status": "refused",
                "type": "advisory",
                "answer": "I'm a facts-only assistant and cannot provide investment advice, opinions, or recommendations.",
                "citation": None,
                "educational_link": "https://www.amfiindia.com/investor-corner/knowledge-center",
                "footer": "Facts-only. No investment advice.",
            }

        # 4. Off-Topic Check (Relevance / Domain Check)
        if self._is_off_topic(cleaned_query):
            return {
                "status": "refused",
                "type": "off_topic",
                "answer": "I can only assist with factual queries regarding the 5 supported HDFC Mutual Fund schemes and general AMC processes. Please ask a factual question about HDFC mutual funds.",
                "citation": None,
                "educational_link": None,
                "footer": "Facts-only. No investment advice.",
            }

        # Passes all guardrails
        return None

    def _contains_pii(self, query: str) -> bool:
        """Check if query contains PII patterns."""
        if self.PAN_PATTERN.search(query):
            return True
        if self.AADHAAR_PATTERN.search(query):
            return True
        if self.EMAIL_PATTERN.search(query):
            return True
        if self.PHONE_PATTERN.search(query):
            return True
        if self.OTP_PATTERN.search(query):
            return True
        return False

    def _is_advisory(self, query: str) -> bool:
        """Check if query contains investment advice intent."""
        query_lower = query.lower()
        for phrase in self.ADVISORY_PHRASES:
            if phrase in query_lower:
                return True
        return False

    def _contains_profanity(self, query: str) -> bool:
        """Check if query contains inappropriate language."""
        query_words = re.findall(r"\b\w+\b", query.lower())
        for word in query_words:
            if word in self.PROFANITY_WORDS:
                return True
        return False

    def _is_off_topic(self, query: str) -> bool:
        """Classify query as off-topic if it lacks domain keywords or references other AMCs."""
        query_lower = query.lower()
        
        # Tokenize query into words
        words = set(re.findall(r"\b\w+\b", query_lower))
        if not words:
            return True
            
        # Check if query references other unsupported AMCs
        if words.intersection(self.UNSUPPORTED_AMCS):
            return True
            
        # Check if there is any intersection with on-topic keywords
        intersection = words.intersection(self.ON_TOPIC_KEYWORDS)
        if len(intersection) > 0:
            return False
            
        # Also check for multi-word phrases (e.g. "capital gain", "how to")
        for phrase in ["capital gain", "how to", "mid cap", "large cap", "tax saver"]:
            if phrase in query_lower:
                return False
                
        return True

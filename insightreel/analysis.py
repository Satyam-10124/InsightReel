"""Key concept extraction from transcripts.

Analyzes transcript text to derive keywords, domain concepts, technical terms,
and action verbs. Designed to be fast and dependency-light.
"""
from __future__ import annotations
import re
from collections import Counter
from typing import Dict, List


def extract_key_concepts(transcripts: List[dict]) -> Dict[str, object]:
    """Extract meaningful key concepts from transcripts.

    Returns a dictionary containing:
      - keywords: list[(keyword, count)]
      - domain_concepts: list[(concept, count)]
      - technical_terms: list[str]
      - action_words: list[str]
      - total_words, unique_words, complexity_score
    """
    if not transcripts:
        return {
            "keywords": [],
            "domain_concepts": [],
            "technical_terms": [],
            "action_words": [],
            "total_words": 0,
            "unique_words": 0,
            "complexity_score": 0.0,
        }

    full_text = " ".join([str(t.get("text", "")) for t in transcripts])

    stop_words = {
        "the",
        "is",
        "at",
        "which",
        "on",
        "and",
        "a",
        "to",
        "are",
        "as",
        "was",
        "will",
        "an",
        "be",
        "or",
        "by",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
        "my",
        "your",
        "his",
        "its",
        "our",
        "their",
        "am",
        "is",
        "are",
        "was",
        "were",
        "being",
        "been",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "not",
        "no",
        "yes",
        "but",
        "if",
        "then",
        "else",
        "when",
        "where",
        "why",
        "how",
        "what",
        "who",
        "whom",
        "whose",
        "because",
        "since",
        "for",
        "now",
        "here",
        "there",
        "today",
        "tomorrow",
        "yesterday",
        "again",
        "also",
        "still",
        "just",
        "only",
        "even",
        "very",
        "really",
        "quite",
        "so",
        "too",
        "more",
        "most",
        "much",
        "many",
        "little",
        "few",
        "some",
        "any",
        "all",
        "going",
        "get",
        "got",
        "getting",
        "goes",
        "went",
        "come",
        "came",
        "coming",
        "comes",
        "put",
        "puts",
        "putting",
        "take",
        "takes",
        "taking",
        "took",
        "make",
        "makes",
        "making",
        "made",
        "give",
        "gives",
        "giving",
        "gave",
        "see",
        "sees",
        "seeing",
        "saw",
        "look",
        "looks",
        "looking",
        "looked",
        "want",
        "wants",
        "wanted",
        "wanting",
        "know",
        "knows",
        "knowing",
        "knew",
        "think",
        "thinks",
        "thinking",
        "thought",
        "say",
        "says",
        "saying",
        "said",
        "tell",
        "tells",
        "telling",
        "told",
        "ask",
        "asks",
        "asking",
        "asked",
        "work",
        "works",
        "working",
        "worked",
        "try",
        "tries",
        "trying",
        "tried",
        "use",
        "uses",
        "using",
        "used",
        "need",
        "needs",
        "needing",
        "needed",
        "like",
        "likes",
        "liking",
        "liked",
        "well",
        "good",
        "better",
        "best",
        "bad",
        "worse",
        "worst",
        # Additional vague/common video terms
        "with",
        "without",
        "within",
        "out",
        "different",
        "same",
        "other",
        "another",
        "each",
        "every",
        "both",
        "either",
        "neither",
        "between",
        "among",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "around",
        "about",
        "into",
        "onto",
        "upon",
        "across",
        "under",
        "over",
        "from",
        "off",
        "back",
        "away",
        "thing",
        "things",
        "something",
        "anything",
        "nothing",
        "everything",
        "someone",
        "anyone",
        "everyone",
        "way",
        "ways",
        "right",
        "left",
        "first",
        "last",
        "next",
        "new",
        "old",
        "big",
        "small",
        "long",
        "short",
        "video",
        "tutorial",
        "today",
        "going",
        "show",
        "example",
    }

    business_concept_patterns = [
        r"\b(?i:(?:Claude\s*Code|Cursor\s*AI|GitHub\s*Copilot|AI\s*agent|code\s*assistant)\s*(?:for|in|with)?\s*(?:development|productivity|automation|workflow|efficiency)?)\b",
        r"\b(?i:(?:developer|development|coding)\s*(?:productivity|efficiency|automation|workflow|assistance|acceleration))\b",
        r"\b(?i:(?:AI-powered|AI-assisted|automated)\s*(?:development|coding|file\s*editing|code\s*review|software\s*development))\b",
        r"\b(?i:(?:medical|dental|healthcare|clinic|practice|patient|doctor|physician|appointment|consultation|insurance|coverage|HIPAA|compliance)\s*(?:automation|system|management|workflow|process|integration|software)?)\b",
        r"\b(?i:(?:patient|lead)\s*(?:qualification|generation|management|follow-up|conversion|interaction|booking|scheduling))\b",
        r"\b(?i:AI\s*(?:agent|assistant|bot|call|phone|voice|automation|system|workflow|integration|powered|driven))\b",
        r"\b(?i:(?:automated|automatic)\s*(?:booking|scheduling|appointment|call|follow-up|lead|response|workflow|process))\b",
        r"\b(?i:(?:voice|phone|call)\s*(?:agent|automation|system|integration|workflow|processing|handling))\b",
        r"\b(?i:(?:sales|marketing|business|customer|client)\s*(?:automation|process|funnel|pipeline|strategy|workflow|management|system))\b",
        r"\b(?i:(?:CRM|database|data)\s*(?:integration|management|storage|workflow|automation|system|processing))\b",
        r"\b(?i:(?:real-time|24/7|round-the-clock)\s*(?:automation|processing|system|workflow|operation|monitoring))\b",
        r"\b(?i:(?:no-code|low-code|workflow|API|webhook|database)\s*(?:automation|integration|deployment|framework|solution|platform))\b",
        r"\b(?i:(?:terminal\s*commands|file\s*editing|code\s*generation|agent\s*automation|development\s*workflow))\b",
    ]

    meaningful_concepts: List[str] = []
    for pattern in business_concept_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = " ".join(match)
            cleaned_match = " ".join(str(match).split())
            if len(cleaned_match) > 3:
                meaningful_concepts.append(cleaned_match.lower())

    concept_counts = Counter(meaningful_concepts)
    domain_concepts = [(concept, count) for concept, count in concept_counts.most_common(8) if count >= 1]

    words = re.findall(r"\b[a-zA-Z]{4,}\b", full_text.lower())
    meaningful_words = [w for w in words if w not in stop_words]
    word_counts = Counter(meaningful_words)
    significant_keywords = [
        (w, c) for w, c in word_counts.most_common(15) if c >= 3 and len(w) > 4
    ]

    combined_topics = domain_concepts + significant_keywords[:5]

    technical_patterns = [
        r"\b(?i:Claude\s*Code|Cursor\s*AI|GitHub\s*Copilot|AI\s*agent|code\s*assistant|development\s*agent)\b",
        r"\b(?i:VS\s*Code|terminal\s*commands|file\s*editing|code\s*review|PR\s*automation)\b",
        r"\b(?i:Twilio|Supabase|Airtable|Zapier|Shopify|Stripe|PayPal|Zoom|Slack|Discord|Notion|Retool|Bubble)\b",
        r"\b(?i:HubSpot|Salesforce|Mailchimp|ConvertKit|GoHighLevel|ActiveCampaign|Klaviyo)\b",
        r"\b(?i:OpenAI|ChatGPT|GPT|Claude|Anthropic|Whisper|Assembly|Deepgram|ElevenLabs|Vapi)\b",
        r"\b(?i:API|SDK|REST|GraphQL|JWT|OAuth|JSON|XML|CSV|HTML|CSS|JavaScript|Python|React|Vue|Angular|Node\.?js|PHP)\b",
        r"\b(?i:Firebase|MongoDB|PostgreSQL|MySQL|Redis|AWS|Azure|Google\s*Cloud)\b",
        r"\b(?i:CRM|ERP|CMS|LMS|ATS|POS|ROI|KPI|SaaS|B2B|B2C|HIPAA)\b",
        r"\b(?i:workflow\s*automation|productivity\s*tool|development\s*efficiency|code\s*generation|agent\s*automation)\b",
        r"\b(?i:EMR|EHR|HL7|FHIR|telehealth|telemedicine|patient\s*portal)\b",
    ]

    technical_terms: List[str] = []
    for pattern in technical_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        for m in matches:
            s = str(m).strip()
            if len(s) > 1:
                technical_terms.append(s)

    seen = set()
    clean_tech: List[str] = []
    for term in technical_terms:
        tl = term.lower()
        if tl not in seen and len(term) > 1:
            seen.add(tl)
            clean_tech.append(term)

    action_patterns = [
        r"\b(?i:implement|deploy|integrate|automate|configure|setup|build|create|develop|design|optimize)\b",
        r"\b(?i:schedule|booking|qualify|convert|track|monitor|analyze|process|manage|handle)\b",
        r"\b(?i:streamline|enhance|improve|scale|customize|connect|sync|generate|execute)\b",
    ]

    action_words: List[str] = []
    for pattern in action_patterns:
        action_words.extend([m.lower() for m in re.findall(pattern, full_text, re.IGNORECASE)])
    action_words = list(set(action_words))

    return {
        "keywords": combined_topics[:10],
        "domain_concepts": domain_concepts,
        "technical_terms": clean_tech[:12],
        "action_words": action_words[:10],
        "total_words": len(words),
        "unique_words": len(set(words)),
        "complexity_score": (len(set(words)) / len(words)) if words else 0.0,
    }

"""Summary generation for InsightReel.

Creates either AI-enhanced summaries (via AiClient) or a clean, structured
basic summary when AI is unavailable.
"""
from __future__ import annotations
from typing import Dict, List, Optional
import time
import re

from .ai import AiClient


def _build_prompt(
    transcripts: List[dict],
    video_title: str,
    video_url: str,
    duration_str: str,
    key_concepts: Dict[str, object],
    user_profile: Dict[str, object],
) -> str:
    full_transcript = "\n\n".join([f"[{t['timestamp']}] {t['text']}" for t in transcripts])

    user_focus_map = {
        "student": "learning objectives, practical applications, study tips",
        "professional": "business value, ROI, implementation strategies",
        "developer": "technical implementation, tools, best practices",
        "entrepreneur": "business opportunities, growth strategies, revenue models",
        "researcher": "methodology, evidence, theoretical frameworks",
        "general": "clear explanations, practical insights, actionable takeaways",
    }
    length_guide = {
        "quick": "Be concise and focus on key points only.",
        "standard": "Provide balanced detail with clear explanations.",
        "detailed": "Offer comprehensive analysis with examples and insights.",
    }

    focus_areas = user_focus_map.get(str(user_profile.get("type", "general")), user_focus_map["general"])    
    length_desc = length_guide.get(str(user_profile.get("length", "standard")), length_guide["standard"])  

    prompt = f"""
Create a personalized summary for a {user_profile.get('name','User')}.

**VIDEO:** {video_title}
**FOCUS:** {focus_areas}
**LENGTH:** {length_desc}
{f"**SPECIAL FOCUS:** {user_profile.get('focus')}" if user_profile.get('focus') else ""}

**KEY CONCEPTS:**
- Main topics: {', '.join([kw[0] for kw in key_concepts.get('keywords', [])[:5]])}
- Technical terms: {', '.join(key_concepts.get('technical_terms', [])[:5])}
- Action words: {', '.join(key_concepts.get('action_words', [])[:5])}

**TRANSCRIPT:**
{full_transcript}

Create a structured summary with:
1. Compelling overview
2. Clear sections with emojis
3. Actionable insights for the {user_profile.get('name','User')}
4. Next steps or recommendations
"""
    return prompt


def _basic_segments(transcripts: List[dict], user_profile: Dict[str, object], key_concepts: Dict[str, object]) -> str:
    segment_count = {"quick": 3, "standard": 5, "detailed": 7}.get(
        str(user_profile.get("length", "standard")), 5
    )
    segment_count = min(segment_count, len(transcripts))
    out = []
    if segment_count <= 0:
        return ""
    step = max(1, len(transcripts) // segment_count)
    for i in range(0, len(transcripts), step):
        if i < len(transcripts):
            t = transcripts[i]
            max_chars = {"quick": 200, "standard": 350, "detailed": 500}.get(
                str(user_profile.get("length", "standard")), 350
            )
            text = str(t.get("text", ""))
            if len(text) > max_chars:
                truncated = text[:max_chars]
                last_period = truncated.rfind(".")
                last_exclamation = truncated.rfind("!")
                last_question = truncated.rfind("?")
                break_point = max(last_period, last_exclamation, last_question)
                if break_point > max_chars * 0.7:
                    text = text[: break_point + 1]
                else:
                    last_space = truncated.rfind(" ")
                    if last_space > max_chars * 0.8:
                        text = text[:last_space] + "..."
                    else:
                        text = truncated + "..."
            segment_title = f"Key Segment ({t['timestamp']})"
            text_lower = text.lower()
            if any(w in text_lower for w in ["introduction", "intro", "welcome", "start", "overview"]):
                segment_title = f"Introduction ({t['timestamp']})"
            elif any(w in text_lower for w in ["conclusion", "summary", "wrap", "end", "final"]):
                segment_title = f"Conclusion ({t['timestamp']})"
            elif any(w in text_lower for w in ["demo", "demonstration", "example", "show", "tutorial"]):
                segment_title = f"Demonstration ({t['timestamp']})"
            elif any(w in text_lower for w in ["implement", "setup", "configure", "build", "create"]):
                segment_title = f"Implementation ({t['timestamp']})"
            elif any(tech.lower() in text_lower for tech in key_concepts.get("technical_terms", [])[:5]):
                segment_title = f"Technical Details ({t['timestamp']})"
            out.append(f"### 🔸 {segment_title}\n\n{text}\n")
    return "\n".join(out)


def create_basic_summary(
    transcripts: List[dict],
    video_title: str,
    video_url: str,
    duration_str: str,
    key_concepts: Dict[str, object],
    user_profile: Dict[str, object],
) -> str:
    icon = str(user_profile.get("icon", "📺"))
    user_name = str(user_profile.get("name", "User"))

    # Topics
    topics: List[str] = []
    if key_concepts.get("domain_concepts"):
        topics.extend([c for c, _ in key_concepts["domain_concepts"][:5]])
    if len(topics) < 5 and key_concepts.get("keywords"):
        for kw, _ in key_concepts["keywords"]:
            if isinstance(kw, str) and len(kw) > 4 and kw not in topics:
                topics.append(kw)
            if len(topics) >= 5:
                break
    if not topics:
        topics = ["automation systems", "workflow integration", "business processes"]

    header = f"""# {icon} {video_title}

> **Personalized for**: {user_name} | **Length**: {str(user_profile.get('length','standard')).title()}
{f"> **Focus**: {user_profile.get('focus')}" if user_profile.get('focus') else ""}

*🔗 [Watch Video]({video_url})*

## 🎯 Overview for {user_name}

**📋 Main Topics**: {', '.join(topics[:5])}

**🛠️ Technical Elements**: {', '.join(set(key_concepts.get('technical_terms', [])[:6])) if key_concepts.get('technical_terms') else 'General automation and integration tools'}

**⚡ Key Actions**: {', '.join(key_concepts.get('action_words', [])[:6]) if key_concepts.get('action_words') else 'Implementation and process optimization'}

## 📝 Content Breakdown
"""

    segments = _basic_segments(transcripts, user_profile, key_concepts)

    analytics = f"""
---

## 📊 Video Analytics
- **Duration**: {duration_str}
- **Segments**: {len(transcripts)}
- **Word count**: {key_concepts.get('total_words',0):,}
- **Main topics**: {', '.join([kw[0] for kw in key_concepts.get('keywords', [])[:5]])}
- **Technical terms**: {', '.join(key_concepts.get('technical_terms', [])[:5]) if key_concepts.get('technical_terms') else 'None'}
- **Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}

---

*🔧 Enhanced analysis (AI unavailable)*
*💡 Add GEMINI_API_KEY for AI-powered summaries*
*🎯 Intelligently analyzed for {icon} {user_name}*
"""

    return header + "\n" + segments + "\n" + analytics


def create_ai_summary(
    transcripts: List[dict],
    video_title: str,
    video_url: str,
    duration_str: str,
    key_concepts: Dict[str, object],
    user_profile: Dict[str, object],
    ai: AiClient,
) -> Optional[str]:
    if not ai.enabled:
        return None
    prompt = _build_prompt(transcripts, video_title, video_url, duration_str, key_concepts, user_profile)
    return ai.generate(prompt)


def create_summary(
    transcripts: List[dict],
    video_title: str,
    video_url: str,
    duration_str: str,
    key_concepts: Dict[str, object],
    user_profile: Dict[str, object],
    ai: Optional[AiClient] = None,
) -> str:
    """Create best-available summary using AI if enabled, else basic."""
    if not transcripts:
        return "# Error\n\nNo transcript available for summarization."

    ai = ai or AiClient()
    ai_text = create_ai_summary(transcripts, video_title, video_url, duration_str, key_concepts, user_profile, ai)
    if ai_text:
        final = f"""# {user_profile.get('icon','📺')} {video_title}

> **Personalized for**: {user_profile.get('name','User')} | **Length**: {str(user_profile.get('length','standard')).title()}
{f"> **Focus**: {user_profile.get('focus')}" if user_profile.get('focus') else ""}

*🔗 [Watch Video]({video_url})*

{ai_text}

---

## 📊 Video Analytics
- **Duration**: {duration_str}
- **Segments**: {len(transcripts)}
- **Word count**: {key_concepts.get('total_words',0):,}
- **Main topics**: {', '.join([kw[0] for kw in key_concepts.get('keywords', [])[:5]])}
- **Technical terms**: {', '.join(key_concepts.get('technical_terms', [])[:5]) if key_concepts.get('technical_terms') else 'None'}
- **Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}

---

*🎯 AI-Enhanced summary by InsightReel*
"""
        return final

    return create_basic_summary(transcripts, video_title, video_url, duration_str, key_concepts, user_profile)

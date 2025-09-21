"""User preferences utilities for InsightReel.

Provides constants and CLI helpers for collecting a user profile
that drives the personalization of summaries.
"""
from __future__ import annotations
from typing import Dict, Optional

USER_TYPES: Dict[int, Dict[str, str]] = {
    1: {"type": "student", "name": "Student", "icon": "🎓"},
    2: {"type": "professional", "name": "Business Professional", "icon": "💼"},
    3: {"type": "developer", "name": "Developer", "icon": "🔧"},
    4: {"type": "entrepreneur", "name": "Entrepreneur", "icon": "🚀"},
    5: {"type": "researcher", "name": "Researcher", "icon": "📚"},
    6: {"type": "general", "name": "General Audience", "icon": "🌟"},
}

LENGTH_TYPES = {1: "quick", 2: "standard", 3: "detailed"}


def prompt_user_profile(input_fn=input, print_fn=print) -> Dict[str, Optional[str]]:
    """Interactive CLI prompt for user profile.

    Returns a dict with keys: type, name, icon, length, focus
    """
    print_fn("\n🎯 Let's personalize your summary!")
    print_fn("=" * 40)

    print_fn("\n👤 What's your role/background?")
    print_fn("1. 🎓 Student")
    print_fn("2. 💼 Business Professional")
    print_fn("3. 🔧 Developer/Technical")
    print_fn("4. 🚀 Entrepreneur")
    print_fn("5. 📚 Researcher")
    print_fn("6. 🌟 General Audience")

    while True:
        try:
            choice = int(input_fn("\nSelect your profile (1-6): ").strip())
            if 1 <= choice <= 6:
                break
            print_fn("❌ Please enter a number between 1-6")
        except ValueError:
            print_fn("❌ Please enter a valid number")

    profile = USER_TYPES[choice].copy()

    print_fn(f"\n📝 Summary length for {profile['name']}:")
    print_fn("1. ⚡ Quick (Key points - 2-3 min read)")
    print_fn("2. 📋 Standard (Balanced - 5-7 min read)")
    print_fn("3. 📖 Detailed (Comprehensive - 10+ min read)")

    while True:
        try:
            length_choice = int(input_fn("\nSelect length (1-3): ").strip())
            if 1 <= length_choice <= 3:
                break
            print_fn("❌ Please enter 1, 2, or 3")
        except ValueError:
            print_fn("❌ Please enter a valid number")

    profile["length"] = LENGTH_TYPES[length_choice]

    specific_focus = input_fn("\n🎯 Any specific focus areas? (optional) ").strip()
    profile["focus"] = specific_focus if specific_focus else None

    print_fn(
        f"\n✅ Profile set: {profile['icon']} {profile['name']} | {profile['length'].title()}"
    )
    if profile["focus"]:
        print_fn(f"🎯 Focus: {profile['focus']}")
    print_fn("")

    return profile

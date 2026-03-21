# linkedin_agent/generator.py
"""Generates 8-week post batches (slot plan + per-post Claude calls)."""
from __future__ import annotations
import json
import re
from pathlib import Path


_CONTENT_MIX = {
    "contrarian": 10,        # ~40% of 24
    "behind-the-scenes": 7,  # ~30%
    "how-to": 5,             # ~20%
    "story": 2,              # ~10%
}


def build_slot_plan(
    strategy_md: str,
    niche: str,
    claude_client,
    web_client,
) -> list[dict]:
    """
    Returns list of 24 slot dicts:
    {week, position, hook_type, topic}
    Weeks 1-8, positions 1-3 per week (3 posts/week × 8 weeks = 24).
    """
    trend_context = web_client.search(f"{niche} news this week") or ""

    # Build week/position skeleton
    skeleton = []
    hook_types = []
    for hook, count in _CONTENT_MIX.items():
        hook_types.extend([hook] * count)
    # Distribute evenly: alternate hook types across weeks
    for i, hook in enumerate(hook_types):
        week = (i // 3) + 1
        position = (i % 3) + 1
        skeleton.append({"week": week, "position": position, "hook_type": hook})

    user = f"""You are a LinkedIn content strategist for {niche}.

CONTENT STRATEGY:
{strategy_md[:1500]}

CURRENT TRENDS:
{trend_context}

Assign a specific, engaging topic to each of these 24 post slots.
Vary topics across weeks. Make topics timely and relevant to {niche}.

Return a JSON array of 24 objects, each with "hook_type" and "topic" keys only.
Do not include week or position — just the 24 objects in order.
"""
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": user}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"```\w*\n?", "", raw).strip().rstrip("```").strip()
    topics = json.loads(raw)

    slots = []
    for i, (skel, topic_data) in enumerate(zip(skeleton, topics)):
        slots.append({
            "week": skel["week"],
            "position": skel["position"],
            "hook_type": topic_data.get("hook_type", skel["hook_type"]),
            "topic": topic_data.get("topic", f"Topic {i+1}"),
        })
    return slots


def generate_posts(
    cycle_dir: str,
    slots: list[dict],
    strategy_md: str,
    voice_posts: list[dict],
    claude_client,
    web_client,
) -> None:
    """
    Generate one markdown file per slot in cycle_dir.
    Skips slots where the file already exists (resume on interrupt).
    """
    out = Path(cycle_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Pick 5 shortest voice examples by character count (practical proxy for token count)
    sorted_posts = sorted(voice_posts, key=lambda p: len(p.get("text", "")))
    examples = sorted_posts[:5]
    voice_section = "\n\n---\n\n".join(p["text"] for p in examples)

    for slot in slots:
        week = slot["week"]
        pos = slot["position"]
        filename = f"week-{week:02d}-post-{pos}.md"
        dest = out / filename
        if dest.exists():
            continue  # resume: skip already-generated posts

        news = web_client.search(f"{slot['topic']} news this week") or ""
        image_data = web_client.image_search(slot.get("image_query", slot["topic"]))

        user = f"""Write a LinkedIn post for a {slot['hook_type']} style post.

TOPIC: {slot['topic']}
WEEK: {week} of 8, POST: {pos} of 3

CONTENT STRATEGY (follow this voice and mix):
{strategy_md[:800]}

VOICE EXAMPLES (match this author's style):
{voice_section[:600]}

CURRENT NEWS HOOK:
{news[:200]}

Instructions:
- Write the post body only (no frontmatter, no title)
- 150-300 words
- Strong opening hook
- Conversational, not corporate
- End with a question or CTA
- On the last line, write: image_query: <3-5 word image search query>
"""
        response = claude_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": user}],
        )
        full_text = response.content[0].text.strip()

        # Extract image_query from last line
        image_query = slot["topic"]
        lines = full_text.splitlines()
        if lines and lines[-1].startswith("image_query:"):
            image_query = lines[-1].split(":", 1)[1].strip()
            post_body = "\n".join(lines[:-1]).strip()
        else:
            post_body = full_text

        if image_data is None:
            image_url = "null  # MANUAL"
            image_credit = "null  # MANUAL"
        else:
            image_url = image_data["url"]
            credit_parts = []
            if image_data.get("photographer"):
                credit_parts.append(f"Photo by {image_data['photographer']}")
            if image_data.get("source_domain"):
                credit_parts.append(f"on {image_data['source_domain']}")
            image_credit = " ".join(credit_parts) if credit_parts else "null"

        md = f"""---
week: {week}
post: {pos}
topic: {slot['topic']}
hook_type: {slot['hook_type']}
status: draft
published_text_snippet: ""
published_url: ""
image_url: {image_url}
image_credit: "{image_credit}"
image_query: "{image_query}"
---

{post_body}
"""
        dest.write_text(md)

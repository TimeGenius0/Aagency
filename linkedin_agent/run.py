# linkedin_agent/run.py
"""CLI orchestrator: init | generate | review"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from linkedin_agent.web import WebClient
from linkedin_agent.scraper import scrape_posts, parse_raw_posts
from linkedin_agent.analyzer import analyze_posts
from linkedin_agent.strategist import build_strategy, update_strategy
from linkedin_agent.generator import build_slot_plan, generate_posts
from linkedin_agent.reviewer import collect_ratings


def _make_clients():
    """Load env and return (anthropic_client, web_client)."""
    load_dotenv()
    import anthropic
    claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    web = WebClient(openclaw_api_key=os.environ.get("OPENCLAW_API_KEY", ""))
    return claude, web


def _read_state(state_dir: str, filename: str) -> str:
    return (Path(state_dir) / filename).read_text().strip()


def _write_state(state_dir: str, filename: str, content: str) -> None:
    path = Path(state_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def run_init(
    landing_page_url: str,
    linkedin_url: str,
    niche: str,
    state_dir: str,
    force: bool = False,
) -> None:
    state = Path(state_dir)
    if state.exists() and not force:
        print(f"ERROR: {state_dir} already exists. Pass --force to overwrite.", file=sys.stderr)
        sys.exit(1)
    state.mkdir(parents=True, exist_ok=True)
    (state / ".auth").mkdir(exist_ok=True)

    claude, web = _make_clients()

    print("[1/6] Fetching landing page...")
    landing_text = web.fetch(landing_page_url) or ""

    print("[2/6] Scraping LinkedIn posts...")
    auth_path = str(state / ".auth" / "linkedin.json")
    raw_posts_path = str(state / "raw-posts.txt")
    try:
        posts = scrape_posts(linkedin_url, auth_path)
    except RuntimeError as e:
        print(f"\nWARNING: {e}")
        print(f"\nManually populate {raw_posts_path} in this format:")
        print("---\ndate: 2026-01-15\nlikes: 42\ncomments: 7\ntext:\nYour post text here.\n---")
        input("\nPress Enter once you have populated raw-posts.txt...")
        posts = parse_raw_posts(raw_posts_path)
        if not posts:
            print("ERROR: No posts found in raw-posts.txt. Exiting.", file=sys.stderr)
            sys.exit(1)

    print("[3/6] Analyzing posts...")
    analysis = analyze_posts(posts, niche, claude, web)

    print("[4/6] Building strategy...")
    build_strategy(landing_text, analysis, niche, state_dir, cycle=1, claude_client=claude)

    print("[5/6] Setting up cycle 1...")
    _write_state(state_dir, "current-cycle.txt", "1")
    _write_state(state_dir, "niche.txt", niche)
    _write_state(state_dir, "linkedin-url.txt", linkedin_url)
    cycle_dir = state / "cycle-01"
    cycle_dir.mkdir(exist_ok=True)

    print("[6/6] Generating slot plan and 24 posts...")
    strategy_md = (state / "strategy.md").read_text()
    slots = build_slot_plan(strategy_md, niche, claude, web)
    (cycle_dir / "slot-plan.json").write_text(json.dumps(slots, indent=2))

    # Use shortest 5 posts for voice calibration
    voice_posts = sorted(posts, key=lambda p: len(p.get("text", "")))[:5]
    generate_posts(str(cycle_dir), slots, strategy_md, voice_posts, claude, web)

    print(f"\nDone. 24 posts written to {cycle_dir}/")


def run_generate(state_dir: str) -> None:
    state = Path(state_dir)
    n = int(_read_state(state_dir, "current-cycle.txt"))
    niche = _read_state(state_dir, "niche.txt")
    strategy_md = (state / "strategy.md").read_text()

    next_n = n + 1
    next_cycle_label = f"cycle-{next_n:02d}"
    next_cycle_dir = state / next_cycle_label

    # Check for review context from current cycle
    review_path = state / f"cycle-{n:02d}" / "review.md"
    review_context = review_path.read_text() if review_path.exists() else ""

    print(f"[generate] Advancing to cycle {next_n}...")
    _write_state(state_dir, "current-cycle.txt", str(next_n))
    next_cycle_dir.mkdir(exist_ok=True)

    claude, web = _make_clients()

    # Incorporate review context into strategy if available
    effective_strategy = strategy_md
    if review_context:
        effective_strategy += f"\n\n## Previous Cycle Review\n{review_context}"

    # Reuse existing slot plan if interrupted mid-generation
    slot_plan_path = next_cycle_dir / "slot-plan.json"
    if slot_plan_path.exists():
        print(f"[generate] Reusing existing slot plan from {slot_plan_path}")
        slots = json.loads(slot_plan_path.read_text())
    else:
        slots = build_slot_plan(effective_strategy, niche, claude, web)
        slot_plan_path.write_text(json.dumps(slots, indent=2))

    # No voice posts available for generate mode without re-scraping
    generate_posts(str(next_cycle_dir), slots, strategy_md, [], claude, web)
    print(f"Done. 24 posts written to {next_cycle_dir}/")


def run_review(state_dir: str) -> None:
    state = Path(state_dir)
    n = int(_read_state(state_dir, "current-cycle.txt"))
    niche = _read_state(state_dir, "niche.txt")
    cycle_label = f"cycle-{n:02d}"
    cycle_dir = state / cycle_label
    auth_path = str(state / ".auth" / "linkedin.json")

    print(f"[review] Reviewing cycle {n}...")

    # Re-scrape engagement data if linkedin-url.txt exists
    linkedin_url_path = state / "linkedin-url.txt"
    scraped_posts = []
    if linkedin_url_path.exists():
        linkedin_url = linkedin_url_path.read_text().strip()
        try:
            scraped_posts = scrape_posts(linkedin_url, auth_path)
        except RuntimeError as e:
            print(f"WARNING: Scrape failed — {e}")
            print("Proceeding with ratings-only review (no engagement data).")

    collect_ratings(str(cycle_dir), scraped_posts)

    review_md = (cycle_dir / "review.md").read_text()

    claude, _ = _make_clients()
    print("[review] Updating strategy...")
    update_strategy(review_md, niche, state_dir, cycle=n, claude_client=claude)

    print("[review] Generating next cycle...")
    run_generate(state_dir)


def main():
    parser = argparse.ArgumentParser(prog="linkedin-agent")
    sub = parser.add_subparsers(dest="mode", required=True)

    init_p = sub.add_parser("init")
    init_p.add_argument("landing_page_url")
    init_p.add_argument("linkedin_url")
    init_p.add_argument("--niche", required=True)
    init_p.add_argument("--force", action="store_true")
    init_p.add_argument("--state-dir", default="state")

    gen_p = sub.add_parser("generate")
    gen_p.add_argument("--state-dir", default="state")

    rev_p = sub.add_parser("review")
    rev_p.add_argument("--state-dir", default="state")

    args = parser.parse_args()
    if args.mode == "init":
        run_init(args.landing_page_url, args.linkedin_url, args.niche,
                 args.state_dir, force=args.force)
    elif args.mode == "generate":
        run_generate(args.state_dir)
    elif args.mode == "review":
        run_review(args.state_dir)


if __name__ == "__main__":
    main()

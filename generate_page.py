#!/usr/bin/env python3
"""
Aagency landing page generator.

Usage:
  python generate_page.py resume.txt services.txt targets.txt [options]

Options:
  --photo PATH_OR_URL   Expert headshot. Local file path or remote URL.
                        If a local file, it is copied into the output folder.
  --directions FILE     Plain-text file with extra instructions for Claude
                        (tone, emphasis, things to highlight or avoid).
  --output DIR          Where to write the generated HTML (default: ./output)

Requires:
  ANTHROPIC_API_KEY (or CLAUDE_API_KEY) in environment or .env file
  pip install anthropic
"""

import sys
import os
import json
import re
import shutil
import argparse
import anthropic


def load_env(path: str):
    """Load key=value pairs from a .env file into os.environ (no overwrite)."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


# Load .env from the script's directory
load_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))


SYSTEM_PROMPT = """You are a copywriter building a personal agency website for a senior expert \
who has launched their own AI-powered agency on Aagency.ai. The site sells their consulting \
services directly to potential clients — it is NOT about the Aagency platform.

Voice: dark, editorial, exclusive, confident. Like a private members club for serious operators. \
No hype, no buzzwords, no clichés. Every sentence earns its place.

STRICT LENGTH RULES — violating any of these produces unusable output:
- hero_philosophy: EXACTLY 1 sentence, 15–22 words. A core belief, not a description.
- expert_short_title: MAX 2 items separated by · (e.g. "Former CPO · AI Founder"). Never more.
- hero_pill_N: 2–4 words max. Short labels, not sentences.
- expert_bio_1/2/3: max 3 sentences each, max 55 words each.
- method_step_desc: EXACTLY 2 sentences. Hard ceiling. Do not write a third.
- service_desc: EXACTLY 2 sentences. Hard ceiling.
- case challenge/approach: EXACTLY 2 sentences each.
- impact_desc: EXACTLY 1 sentence, max 18 words.
- proof_quote: EXACTLY 2 sentences, max 40 words total.
- diff_N_desc: EXACTLY 1–2 sentences.
- client_N_desc: EXACTLY 2 sentences.
- booking_desc: max 2 sentences.

CONTENT RULES:
- All copy tailored to THIS person's career arc — never generic filler
- Headline lines: short, punchy, serif-friendly. No punctuation at line ends except the last
- Headlines spanning multiple lines use literal \\n to separate lines
- trust_employers: real company names from their resume ONLY — no invented or generic entries
- trust_clients: if real named clients exist in the resume, use them; otherwise use short \
  sector labels max 3 words (e.g. "Series B SaaS", "Fintech"). Never mix real and fictional.
- Credential values: max 6 characters (e.g. "$42M", "10×", "4.2M", "80%")
- Agency name: elegant — LastName.ai, LastnameGroup.ai, or domain word + .ai
- stat_1 = $ value per engagement hour; stat_2 = avg weekly hours
- stat_1_label and stat_2_label: max 4 words each

Return ONLY valid JSON. No markdown, no explanation, no code fences."""


USER_PROMPT_TEMPLATE = """{directions}Resume:
{resume}

Services they want to offer:
{services}

Potential target clients:
{targets}

Generate a JSON object with exactly these fields:

{{
  "person_name": "Full Name",
  "person_first_name": "First",
  "agency_name_stem": "Voss",
  "agency_name_tld": "ai",
  "page_title": "Voss.ai — Brand strategy. Scaled by AI.",
  "hero_eyebrow": "By application only · Brand & Growth Strategy",
  "hero_line_1": "First headline line",
  "hero_line_2": "Second headline line",
  "hero_line_3": "Third line — last word can be in <em>italic</em>",
  "hero_philosophy": "One sentence, 15–22 words. Core professional belief — manifesto, not description.",
  "hero_pill_1": "2–4 word label",
  "hero_pill_2": "2–4 word label",
  "hero_pill_3": "2–4 word label",
  "hero_pill_4": "2–4 word label",
  "stat_1_value": 5800,
  "stat_1_prefix": "$",
  "stat_1_suffix": "",
  "stat_1_initial": "$0",
  "stat_1_label": "per hour of expertise",
  "stat_2_value": 4,
  "stat_2_prefix": "",
  "stat_2_suffix": " hrs",
  "stat_2_initial": "0 hrs",
  "stat_2_label": "avg. weekly commitment",
  "trust_employers": ["Employer A", "Employer B"],
  "trust_clients": ["Sector A", "Sector B", "Sector C"],
  "expert_name": "Full Name",
  "expert_short_title": "Former CMO · Brand Strategist",
  "expert_headline": "One or two lines\\nabout their defining expertise",
  "expert_bio_1": "2–3 sentences, max 55 words. Career arc and defining achievement.",
  "expert_bio_2": "2–3 sentences, max 55 words. Specific impact numbers and key roles.",
  "expert_bio_3": "2 sentences, max 40 words. What clients get through this agency.",
  "cred_1_value": "$42M",
  "cred_1_label": "budgets managed",
  "cred_2_value": "60",
  "cred_2_label": "person team built",
  "cred_3_value": "10×",
  "cred_3_label": "user growth driven",
  "cred_4_value": "14",
  "cred_4_label": "market launches",
  "method_headline": "AI agents do the work\\nYou get the expertise\\n<em>without the overhead</em>",
  "method_sub": "1–2 sentences on the AI-agent + expert-supervision model.",
  "method_step_1_title": "Step one title",
  "method_step_1_desc": "EXACTLY 2 sentences on this phase.",
  "method_step_2_title": "Step two title",
  "method_step_2_desc": "EXACTLY 2 sentences.",
  "method_step_3_title": "Step three title",
  "method_step_3_desc": "EXACTLY 2 sentences.",
  "service_1_title": "Primary service name",
  "service_1_desc": "EXACTLY 2 sentences on who this is for and what they get.",
  "service_1_includes": ["Deliverable 1", "Deliverable 2", "Deliverable 3", "Deliverable 4"],
  "service_1_outcome": "Outcome — one crisp sentence describing the end result",
  "service_2_title": "Second service name",
  "service_2_desc": "EXACTLY 2 sentences.",
  "service_2_includes": ["Item 1", "Item 2", "Item 3", "Item 4"],
  "service_2_outcome": "Outcome statement",
  "service_3_title": "Third service name",
  "service_3_desc": "EXACTLY 2 sentences.",
  "service_3_includes": ["Item 1", "Item 2", "Item 3"],
  "service_3_outcome": "Outcome statement",
  "service_4_title": "Fourth service name",
  "service_4_desc": "EXACTLY 2 sentences.",
  "service_4_includes": ["Item 1", "Item 2", "Item 3"],
  "service_4_outcome": "Outcome statement",
  "case_1_client_type": "Client category — e.g. 'Series B Consumer Tech'",
  "case_1_result_big": "4.2M",
  "case_1_result_label": "users acquired in 18 months",
  "case_1_challenge": "EXACTLY 2 sentences on the problem.",
  "case_1_approach": "EXACTLY 2 sentences on how this expert solved it.",
  "case_2_client_type": "Client category",
  "case_2_result_big": "$35B",
  "case_2_result_label": "valuation at reposition",
  "case_2_challenge": "EXACTLY 2 sentences.",
  "case_2_approach": "EXACTLY 2 sentences.",
  "case_3_client_type": "Client category",
  "case_3_result_big": "6",
  "case_3_result_label": "markets launched in 12 months",
  "case_3_challenge": "EXACTLY 2 sentences.",
  "case_3_approach": "EXACTLY 2 sentences.",
  "impact_1_number": "$500M+",
  "impact_1_label": "revenue influenced",
  "impact_1_desc": "1 sentence, max 18 words.",
  "impact_2_number": "14",
  "impact_2_label": "market launches",
  "impact_2_desc": "1 sentence, max 18 words.",
  "impact_3_number": "3",
  "impact_3_label": "companies founded",
  "impact_3_desc": "1 sentence, max 18 words.",
  "impact_4_number": "15+",
  "impact_4_label": "years at the frontier",
  "impact_4_desc": "1 sentence, max 18 words.",
  "diff_headline": "Not a consultancy\\nNot an agency\\n<em>Something sharper</em>",
  "diff_sub": "2 sentences on what genuinely differentiates this person's model.",
  "diff_1_icon": "⌘",
  "diff_1_title": "First differentiator — 3–5 words",
  "diff_1_desc": "1–2 sentences.",
  "diff_2_icon": "◈",
  "diff_2_title": "Second differentiator",
  "diff_2_desc": "1–2 sentences.",
  "diff_3_icon": "◎",
  "diff_3_title": "Third differentiator",
  "diff_3_desc": "1–2 sentences.",
  "diff_4_icon": "⬡",
  "diff_4_title": "Fourth differentiator",
  "diff_4_desc": "1–2 sentences.",
  "proof_1_quote": "EXACTLY 2 sentences, max 40 words. Specific, references real outcomes.",
  "proof_1_name": "First L.",
  "proof_1_title": "Role · Company type",
  "proof_1_result": "$2.1M pipeline generated",
  "proof_1_context": "within 90 days of engagement",
  "proof_2_quote": "EXACTLY 2 sentences, max 40 words.",
  "proof_2_name": "First L.",
  "proof_2_title": "Role · Company type",
  "proof_2_result": "Series B closed at $40M",
  "proof_2_context": "2 months after narrative refresh",
  "proof_3_quote": "EXACTLY 2 sentences, max 40 words.",
  "proof_3_name": "First L.",
  "proof_3_title": "Role · Company type",
  "proof_3_result": "3 markets launched",
  "proof_3_context": "in under 6 months",
  "client_1_icon": "⌘",
  "client_1_type": "Ideal client type — 3–6 words",
  "client_1_desc": "EXACTLY 2 sentences on who they are and why they're the right fit.",
  "client_2_icon": "◈",
  "client_2_type": "Second ideal client type",
  "client_2_desc": "EXACTLY 2 sentences.",
  "client_3_icon": "◎",
  "client_3_type": "Third ideal client type",
  "client_3_desc": "EXACTLY 2 sentences.",
  "booking_headline": "Short punchy\\nbooking headline\\nin three lines",
  "booking_desc": "MAX 2 sentences on what the discovery call covers and what they walk away with.",
  "checklist_1": "First thing they get from the call — max 10 words",
  "checklist_2": "Second item — max 10 words",
  "checklist_3": "Third item — max 10 words",
  "checklist_4": "Fourth item — max 10 words"
}}"""


def read_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def generate_content(resume: str, services: str, targets: str, directions: str = '') -> dict:
    client = anthropic.Anthropic()

    directions_block = ''
    if directions:
        directions_block = f"Additional instructions for this person's page:\n{directions}\n\n"

    user_content = USER_PROMPT_TEMPLATE.format(
        directions=directions_block,
        resume=resume,
        services=services,
        targets=targets,
    )
    print("  Calling Claude API...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=5000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    response_text = message.content[0].text

    # Strip markdown code fences if present
    response_text = re.sub(r'^```(?:json)?\s*', '', response_text.strip())
    response_text = re.sub(r'\s*```$', '', response_text.strip())

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse JSON from Claude response:\n{response_text[:500]}")


def render_trust_companies(employers: list, clients: list) -> str:
    parts = []
    for name in employers:
        parts.append(f'<span class="trust-company employer">{name}</span>')
    for name in clients:
        parts.append(f'<span class="trust-company">{name}</span>')
    return '\n    '.join(parts)


def render_service_includes(items: list) -> str:
    return '\n          '.join(f'<li>{item}</li>' for item in items)


def render_expert_photo(photo_src: str, initials: str) -> str:
    """Return either an <img> tag or the monogram placeholder."""
    if photo_src:
        return f'<img class="expert-photo" src="{photo_src}" alt="">'
    return (
        f'<div class="expert-monogram">'
        f'<span class="expert-monogram-text">{initials}</span>'
        f'</div>'
    )


def get_initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return parts[0][0].upper() + parts[-1][0].upper()
    return parts[0][0].upper() if parts else '?'


def get_initial(name: str) -> str:
    name = name.strip()
    return name[0].upper() if name else '?'


def apply_template(template: str, data: dict, photo_src: str = '') -> str:
    result = template

    # Multi-line headline fields: convert \n to <br/>
    for key in ('expert_headline', 'method_headline', 'diff_headline', 'booking_headline'):
        if key in data:
            data[key] = data[key].replace('\\n', '<br/>').replace('\n', '<br/>')

    # Compute derived fields
    initials = get_initials(data.get('expert_name', ''))
    data['expert_photo_element'] = render_expert_photo(photo_src, initials)
    data['proof_1_initial'] = get_initial(data.get('proof_1_name', ''))
    data['proof_2_initial'] = get_initial(data.get('proof_2_name', ''))
    data['proof_3_initial'] = get_initial(data.get('proof_3_name', ''))

    # Build trust companies HTML
    trust_html = render_trust_companies(
        data.get('trust_employers', []),
        data.get('trust_clients', []),
    )
    result = result.replace('{{TRUST_COMPANIES_HTML}}', trust_html)

    # Build service includes HTML
    for n in range(1, 5):
        key = f'service_{n}_includes'
        items = data.get(key, [])
        html = render_service_includes(items)
        result = result.replace(f'{{{{SERVICE_{n}_INCLUDES_HTML}}}}', html)

    # Replace all scalar placeholders
    for key, value in data.items():
        if isinstance(value, list):
            continue
        placeholder = '{{' + key.upper() + '}}'
        result = result.replace(placeholder, str(value))

    return result


def slugify(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    name = re.sub(r'\s+', '-', name)
    return name


def resolve_photo(photo_arg: str, output_dir: str) -> str:
    """
    If photo_arg is a URL, return it unchanged.
    If it's a local file, copy it into output_dir and return the filename.
    """
    if not photo_arg:
        return ''
    if photo_arg.startswith('http://') or photo_arg.startswith('https://'):
        return photo_arg
    if os.path.isfile(photo_arg):
        filename = os.path.basename(photo_arg)
        dest = os.path.join(output_dir, filename)
        shutil.copy2(photo_arg, dest)
        return filename
    print(f"Warning: photo file not found: {photo_arg}  (monogram will be used instead)")
    return ''


def main():
    parser = argparse.ArgumentParser(
        description='Generate a personalized Aagency landing page.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python generate_page.py resume.txt services.txt targets.txt
  python generate_page.py resume.txt services.txt targets.txt --photo headshot.jpg
  python generate_page.py resume.txt services.txt targets.txt --directions notes.txt
  python generate_page.py resume.txt services.txt targets.txt \\
      --photo https://example.com/photo.jpg --directions notes.txt --output ~/Sites
""",
    )
    parser.add_argument('resume',     help='Path to resume text file')
    parser.add_argument('services',   help='Path to services text file')
    parser.add_argument('targets',    help='Path to target clients text file')
    parser.add_argument(
        '--photo',
        metavar='PATH_OR_URL',
        default='',
        help='Headshot image — local file path or remote URL',
    )
    parser.add_argument(
        '--directions',
        metavar='FILE',
        default='',
        help='Plain-text file with extra instructions for Claude',
    )
    parser.add_argument(
        '--output',
        metavar='DIR',
        default='',
        help='Output directory (default: <script_dir>/output)',
    )
    args = parser.parse_args()

    # API key
    api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('CLAUDE_API_KEY')
    if not api_key:
        print("Error: set ANTHROPIC_API_KEY (or CLAUDE_API_KEY) in your environment or a .env file.")
        sys.exit(1)
    os.environ['ANTHROPIC_API_KEY'] = api_key

    # Validate input files
    for path in (args.resume, args.services, args.targets):
        if not os.path.exists(path):
            print(f"Error: File not found: {path}")
            sys.exit(1)

    # Template
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, 'template.html')
    if not os.path.exists(template_path):
        print(f"Error: template.html not found at {template_path}")
        sys.exit(1)

    # Read inputs
    print("Reading input files...")
    resume     = read_file(args.resume)
    services   = read_file(args.services)
    targets    = read_file(args.targets)
    directions = read_file(args.directions) if args.directions else ''

    if directions:
        print(f"  Using directions from: {args.directions}")

    # Generate
    print("Generating personalized content with Claude...")
    try:
        data = generate_content(resume, services, targets, directions)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Output dir
    output_dir = args.output or os.path.join(script_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    # Resolve photo (copy local files into output dir)
    photo_src = resolve_photo(args.photo, output_dir)
    if photo_src:
        print(f"  Photo: {photo_src}")

    # Render
    print("Rendering template...")
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    html = apply_template(template, data, photo_src)

    person_name = data.get('person_name', 'agency')
    filename = slugify(person_name) + '.html'
    output_path = os.path.join(output_dir, filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✓ Generated: {output_path}")
    print(f"  Agency:    {data.get('agency_name_stem', '')}.{data.get('agency_name_tld', 'ai')}")
    print(f"  Person:    {data.get('person_name', '')}")
    if directions:
        print(f"  Directions applied from: {args.directions}")


if __name__ == '__main__':
    main()

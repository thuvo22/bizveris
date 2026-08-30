#!/usr/bin/env python3
"""
Generate a hosted SMS opt-in page for one BizVeris client.

The page it writes is the verifiable call-to-action a carrier reviewer looks
for during A2P 10DLC campaign registration. Hosting it ourselves removes the
biggest external dependency in onboarding: the client's own website, which
they often cannot edit and sometimes do not have.

Usage:
  python3 optin/new-client.py \
      --slug onpointpros \
      --business "OnPoint Pros" \
      --city "Allen, Texas" \
      --phone "+13465725599" \
      --email onpoint.pros.tx@gmail.com \
      --headline "Text us your project. Get a price range back today." \
      --accent "#B3282D"

Then point the campaign registration's opt-in / CTA field at:
  https://bizveris.com/optin/<slug>/
"""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "_template.html"
# Bump when the consent wording changes, so an older signer's record can never
# be confused with wording introduced after they agreed.
CONSENT_VERSION = "2026-08-30.1"


def pretty_phone(raw: str) -> str:
    d = re.sub(r"\D", "", raw or "")
    d = d[-10:] if len(d) >= 10 else d
    return f"({d[0:3]}) {d[3:6]}-{d[6:10]}" if len(d) == 10 else raw


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help="url segment, a-z0-9 and dashes")
    ap.add_argument("--business", required=True)
    ap.add_argument("--city", required=True, help='e.g. "Allen, Texas"')
    ap.add_argument("--phone", required=True, help="the number that texts customers")
    ap.add_argument("--email", default="")
    ap.add_argument("--headline", default="Text us your project. Get a price range back today.")
    ap.add_argument("--accent", default="#B3282D", help="client brand color for the button")
    a = ap.parse_args()

    slug = re.sub(r"[^a-z0-9-]", "", a.slug.lower())
    if not slug:
        print("slug must contain a-z, 0-9 or dashes", file=sys.stderr)
        return 1
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", a.accent):
        print("accent must be a 6 digit hex color like #B3282D", file=sys.stderr)
        return 1

    html = TEMPLATE.read_text()
    for token, value in {
        "{{SLUG}}": slug,
        "{{BUSINESS}}": a.business,
        "{{CITY}}": a.city,
        "{{PHONE_DISPLAY}}": pretty_phone(a.phone),
        "{{HEADLINE}}": a.headline,
        "{{ACCENT}}": a.accent,
        "{{EMAIL_SUFFIX}}": f" or {a.email}" if a.email else "",
        "{{CONSENT_VERSION}}": CONSENT_VERSION,
    }.items():
        html = html.replace(token, value)

    left = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if left:
        print(f"unfilled tokens: {sorted(set(left))}", file=sys.stderr)
        return 1

    out_dir = HERE / slug
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(html)
    print(f"wrote {out_dir/'index.html'}")
    print(f"live at https://bizveris.com/optin/{slug}/ once pushed")
    print(f"consent version {CONSENT_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

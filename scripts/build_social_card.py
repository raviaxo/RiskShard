#!/usr/bin/env python3
"""Build the social/link-preview card from the repo's own governed data.

The card is what LinkedIn, Reddit, Slack and GitHub render when a RiskShard
link is shared, so its numbers must not drift from reality. Everything on it —
the portfolio totals and the featured evidence row (parameter, value, source,
publication date, verified/estimate tag) — is read live from the same
provenance the explorer uses. Only the editorial choices are configurable:
which shard and parameter to feature, and the headline.

    python scripts/build_social_card.py                 # HTML + PNG (needs Chrome)
    python scripts/build_social_card.py --feature-shard gb_finance_data_breach_midmarket

Writes docs/social-card.html and, when a Chrome/Chromium binary is available,
rasterises it to docs/social-card.png at 1280x640. Rasterising needs a browser
that this project deliberately does not depend on, so on a machine without one
the HTML is still written and the exact command is printed.

Re-run after any evidence change, alongside `build_explorer.py`. `--check`
compares the committed HTML against live data and fails if the card has gone
stale, so drift is caught even when nobody re-rasterises.
"""
import argparse
import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from engine.project_paths import find_project_root  # noqa: E402

ROOT = find_project_root(fallback=SCRIPT_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.provenance import build_portfolio_provenance  # noqa: E402
from engine.risk_modules import find_risk_module  # noqa: E402

TEMPLATE = Path(__file__).resolve().parent / "social_card_template.html"
SITE_URL = "raviaxo.github.io/RiskShard"

# Editorial defaults. The numbers are always generated; these only pick which
# true row to put on the card and how to frame it.
# Rewritten 2026-08-19. The previous card led with "Tell your CEO what it costs" and
# framed the product as a defensible dollar range, which is the simulation-as-product
# framing ADR-0010 retired and ADR-0016 replaced. The card is the first thing a reader
# sees on a shared link, so it was contradicting the page it linked to.
DEFAULT_HEADLINE = "No public source publishes a <em>mode.</em>"

def default_outcome(root=None):
    """The card's own coverage, generated rather than typed.

    This line was hand-written and went stale twice inside three days as the audit
    moved. Every other number on the card is generated from repo data; there was no
    reason this one was not, and a stale denominator on a shared link is the exact
    failure this project exists to argue against.
    """
    from engine.source_audit import build_source_audit
    coverage = build_source_audit(root or ROOT)["coverage"]
    return (
        f"Every risk estimate needs a most-likely loss. We read "
        f"{coverage['sources_fully_verified']} of {coverage['sources']} public cyber-loss "
        f"sources and <b>not one publishes it</b>, so what goes in the slot is a published mean."
    )


DEFAULT_OUTCOME = None  # resolved at build time by default_outcome()
DEFAULT_SHARD = "us_finance_bec_midmarket"
DEFAULT_PARAM = "impact.likely"

CHROME_CANDIDATES = (
    "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


def find_chrome():
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def money(value, currency_hint="$"):
    """Render a currency parameter the way the card shows it: whole units."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{currency_hint}{number:,.0f}"


def featured_row(portfolio, shard_id, parameter):
    for module in portfolio["modules"]:
        if module["module_id"] != shard_id:
            continue
        for card in module["cards"]:
            if card["parameter"] == parameter:
                return card
        raise SystemExit(f"parameter {parameter!r} not found on shard {shard_id!r}")
    raise SystemExit(f"shard {shard_id!r} not found")


def build_fields(root, shard_id, parameter, headline, outcome):
    portfolio = build_portfolio_provenance(root)
    totals = portfolio["totals"]
    card = featured_row(portfolio, shard_id, parameter)
    module = find_risk_module(shard_id, root) or {}
    ctx = module.get("context", {})

    countries = {
        (find_risk_module(m["module_id"], root) or {}).get("context", {}).get("country")
        for m in portfolio["modules"]
    }
    countries.discard(None)

    # Company size stays on the card: the framing is mid-market, not enterprise.
    spec = " · ".join(
        part for part in (
            (ctx.get("country") or "").upper(),
            (ctx.get("industry") or "").replace("_", " "),
            (ctx.get("company_size") or "").replace("_", "-"),
            (module.get("threat") or "").replace("_", " "),
        ) if part
    ).upper()

    backed = card.get("status") == "source_backed"
    value = card.get("value")
    unit = card.get("unit")
    shown = money(value) if unit == "currency" else str(value)

    source = card.get("source_name") or "—"
    published = card.get("publication_date")
    if published:
        source = f"{source} · {_month_year(published)}"

    return {
        "__RS_HEADLINE__": headline,
        "__RS_OUTCOME__": outcome,
        "__RS_SPEC__": html.escape(spec),
        "__RS_PARAM__": html.escape(parameter),
        "__RS_VALUE__": html.escape(shown),
        "__RS_SOURCE__": html.escape(source),
        "__RS_TAG__": "source-backed" if backed else "estimate",
        "__RS_TAGCLASS__": "" if backed else "est",
        "__RS_SHARDS__": str(totals["shards"]),
        "__RS_BACKED__": f"{totals['params_source_backed']} / {totals['params_total']}",
        "__RS_COUNTRIES__": str(len(countries)),
        "__RS_URL__": SITE_URL,
    }


def _month_year(date_string):
    months = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    try:
        year, month, _ = str(date_string).split("-")[:3]
        return f"{months[int(month) - 1]} {year}"
    except (ValueError, IndexError):
        return str(date_string)


def render(fields):
    markup = TEMPLATE.read_text(encoding="utf-8")
    for token, value in fields.items():
        markup = markup.replace(token, value)
    leftover = [token for token in fields if token in markup]
    if leftover:
        raise ValueError(f"template placeholders left unfilled: {leftover}")
    return markup


def rasterise(html_path, png_path, chrome, timeout=60):
    """Screenshot the card with headless Chrome at exactly 1280x640.

    Returns True on success. Headless Chrome can hang when a normal instance of
    the same channel is already running, so failure is reported rather than
    raised — the HTML is the generated artifact, the PNG is a convenience.
    """
    with tempfile.TemporaryDirectory() as profile:
        try:
            subprocess.run(
                [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                 "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                 "--hide-scrollbars", f"--user-data-dir={profile}",
                 "--window-size=1280,640", "--virtual-time-budget=5000",
                 f"--screenshot={png_path}", html_path.as_uri()],
                check=True, capture_output=True, timeout=timeout,
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError):
            return False
    return png_path.exists()


def rasterise_hint(chrome, html_path, png_path):
    binary = chrome or "<chrome>"
    return (f'  "{binary}" --headless=new --window-size=1280,640 '
            f"--screenshot={png_path} {html_path.as_uri()}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the social/link-preview card.")
    parser.add_argument("--feature-shard", default=DEFAULT_SHARD)
    parser.add_argument("--feature-param", default=DEFAULT_PARAM)
    parser.add_argument("--headline", default=DEFAULT_HEADLINE)
    parser.add_argument("--outcome", default=None)
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "social-card.html")
    parser.add_argument("--png", type=Path, default=ROOT / "docs" / "social-card.png")
    parser.add_argument("--check", action="store_true",
                        help="Fail if the committed card no longer matches live data.")
    parser.add_argument("--skip-png", action="store_true",
                        help="Write the HTML only; do not attempt to rasterise.")
    args = parser.parse_args(argv)

    fields = build_fields(ROOT, args.feature_shard, args.feature_param,
                          args.headline, args.outcome or default_outcome(ROOT))
    markup = render(fields)

    if args.check:
        if not args.output.exists():
            print(f"Social card missing: {args.output}")
            return 1
        if args.output.read_text(encoding="utf-8") != markup:
            print("Social card is stale — regenerate: python scripts/build_social_card.py")
            return 1
        print(f"Social card current: {fields['__RS_BACKED__']} source-backed, "
              f"{fields['__RS_SHARDS__']} shards")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markup, encoding="utf-8")
    print(f"Social card HTML written: {args.output}")
    print(f"  featured: {args.feature_shard} / {args.feature_param} = {fields['__RS_VALUE__']}")
    print(f"  totals  : {fields['__RS_BACKED__']} source-backed · {fields['__RS_SHARDS__']} shards"
          f" · {fields['__RS_COUNTRIES__']} countries")

    if args.skip_png:
        return 0

    chrome = find_chrome()
    if chrome and rasterise(args.output, args.png, chrome):
        print(f"Social card PNG written: {args.png}")
        return 0

    reason = "No Chrome/Chromium found" if not chrome else "Headless Chrome did not produce a PNG"
    print(f"{reason} — PNG not regenerated. Rasterise it with:")
    print(rasterise_hint(chrome, args.output, args.png))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

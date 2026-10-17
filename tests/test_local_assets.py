"""Pages must load their styles and fonts without contacting a third-party host."""
from html.parser import HTMLParser
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
OUTSIDE = re.compile(r"^(?:https?:)?//", re.IGNORECASE)
CSS_RESOURCE = re.compile(
    r"(?:url\(\s*[\"']?|@import\s+[\"'])\s*((?:https?:)?//[^\s\"'<>;)]+)",
    re.IGNORECASE,
)


class AssetLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.outside = []

    def handle_starttag(self, tag, attrs):
        # Ordinary links to the source repository are navigation, not page assets.
        attribute = "href" if tag == "link" else "src" if tag in ("script", "img", "iframe") else None
        if attribute:
            url = dict(attrs).get(attribute) or ""
            if OUTSIDE.match(url.strip()):
                self.outside.append(url)


def test_templates_and_static_assets_have_no_outside_font_or_stylesheet_host():
    outside = []
    for directory in ("app/templates", "app/static", "docs"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.suffix not in (".html", ".css", ".js", ".svg"):
                continue
            source = path.read_text(encoding="utf-8")
            links = AssetLinks()
            links.feed(source)
            urls = links.outside + CSS_RESOURCE.findall(source)
            outside.extend(f"{path.relative_to(ROOT)}: {url}" for url in urls)
    assert not outside, "Outside page assets:\n" + "\n".join(outside)

"""A roster name or an error message is text, never markup or script. The name below carries a single quote, a double
quote, a tag and an ampersand: on the eligible list and in the settings message it must come back as the same text,
add no element to the page, and appear in no inline event handler (an HTML-escaped quote is decoded again before an
inline handler runs, so escaping alone does not make a name safe there)."""
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

NAME = "Zoë O'Brien \"<img src=x onerror=alert(1)>\" & Co"


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.tags, self.handlers, self.confirms, self.text = [], [], [], []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        for k, v in attrs:
            if k.startswith("on"):
                self.handlers.append(v or "")
            if k == "data-confirm":
                self.confirms.append(v)

    def handle_data(self, data):
        self.text.append(data)


@pytest.fixture()
def client(data_dir):
    from app import web
    web.app.config.update(TESTING=True)
    return web.app.test_client()


def assert_text_only(html):
    page = Page(html)
    assert "img" not in page.tags, "the name added an element"
    assert not any("Brien" in h for h in page.handlers), "the name is inside an inline handler"
    return page


def test_a_name_with_quotes_on_the_eligible_list_is_text(client):
    from app import database as db, web
    db.upsert_eligible("10000301", NAME, 88.0, "database", [], {})
    page = assert_text_only(client.get(f"/prof/{web.PROF_TOKEN}/eligible").get_data(as_text=True))
    assert NAME in "".join(page.text)
    assert page.confirms == [f"Remove {NAME} from the eligible list?"]


def test_a_removed_name_and_an_error_in_the_settings_message_are_text(client, monkeypatch):
    from app import config, database as db, web
    monkeypatch.setattr(config, "MIN_GRADE_PERCENT", config.MIN_GRADE_PERCENT)
    monkeypatch.setattr(config, "MIN_ATTENDANCE_PERCENT", config.MIN_ATTENDANCE_PERCENT)
    url = f"/prof/{web.PROF_TOKEN}/settings"

    # no enrolments on record, so the student no longer qualifies and the message lists the name
    db.upsert_eligible("10000302", NAME, 88.0, "database", [], {})
    html = client.post(url, data={"min_grade": "80", "min_att": "90", "action": "save_and_recheck"}).get_data(as_text=True)
    page = assert_text_only(html)
    assert f"{NAME} (10000302)" in "".join(page.text)
    assert page.tags.count("br") >= 2, "the message keeps its own line breaks"

    # the exception text quotes the input back
    html = client.post(url, data={"min_grade": NAME, "min_att": "90", "action": "save"}).get_data(as_text=True)
    page = assert_text_only(html)
    assert "Error:" in "".join(page.text) and "Brien" in "".join(page.text)


def test_no_template_writes_a_value_into_an_inline_handler():
    templates = Path(__file__).resolve().parent.parent / "app" / "templates"
    hits = [f"{t.name}: {m.group(0)[:80]}" for t in sorted(templates.glob("*.html"))
            for m in re.finditer(r"\bon[a-z]+=\"[^\"]*\{\{[^\"]*\"", t.read_text(encoding="utf-8"))]
    assert hits == []

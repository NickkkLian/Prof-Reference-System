"""Nothing must leave this machine unless the professor has configured an address and a key. The test replaces
urllib's opener with one that fails loudly, so a request that should not happen shows up as a failure rather than as
a real e-mail — and the one case that does send is checked the same way, by capturing the request instead of making
it."""
import json
import urllib.request

import pytest

from app import config, notifier


@pytest.fixture()
def no_network(monkeypatch):
    """Any HTTP request from here on is a test failure; returns the list of requests that were attempted."""
    attempted = []

    def refuse(req, *a, **kw):
        attempted.append(req)
        raise AssertionError(f"the code tried to reach {req.full_url}")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    return attempted


@pytest.fixture(autouse=True)
def blank_settings(monkeypatch):
    monkeypatch.setattr(config, "load_email_settings", lambda: None)
    monkeypatch.setattr(config, "NOTIFY_EMAIL", "")
    monkeypatch.setattr(config, "BREVO_API_KEY", "")
    monkeypatch.setattr(config, "SENDER_EMAIL", "")


def test_no_address_configured_sends_nothing(no_network):
    ok, message = notifier.send_submission_notification("10000001", "Alice Chen", "10000001_transcript.pdf", "10000001_letter.pdf")
    assert ok is False
    assert "notification email" in message.lower()
    assert attempted_nothing(no_network)


def test_address_but_no_key_sends_nothing(no_network, monkeypatch):
    monkeypatch.setattr(config, "NOTIFY_EMAIL", "prof@example.com")
    ok, message = notifier.send_submission_notification("10000001", "Alice Chen", "10000001_transcript.pdf", "10000001_letter.pdf")
    assert ok is False
    assert "api key" in message.lower()
    assert attempted_nothing(no_network)


def test_the_test_button_is_just_as_quiet(no_network):
    ok, _ = notifier.test_email()
    assert ok is False
    assert attempted_nothing(no_network)


def test_with_both_configured_it_posts_once_to_brevo(monkeypatch):
    """The only case that sends: the request is captured, not made."""
    sent = []

    class Response:
        status = 201
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def capture(req, *a, **kw):
        sent.append(req)
        return Response()

    monkeypatch.setattr(config, "NOTIFY_EMAIL", "prof@example.com")
    monkeypatch.setattr(config, "BREVO_API_KEY", "key-for-the-test")
    monkeypatch.setattr(config, "SENDER_EMAIL", "roster@example.com")
    monkeypatch.setattr(urllib.request, "urlopen", capture)

    ok, message = notifier.send_submission_notification("10000001", "Alice Chen", "10000001_transcript.pdf", "10000001_letter.pdf")
    assert ok is True and "sent" in message.lower()
    assert len(sent) == 1
    req = sent[0]
    assert req.full_url == "https://api.brevo.com/v3/smtp/email"
    assert req.headers["Api-key"] == "key-for-the-test"
    body = json.loads(req.data.decode())
    assert body["to"] == [{"email": "prof@example.com"}]
    assert body["sender"] == {"name": config.APP_NAME, "email": "roster@example.com"}
    assert "10000001" in body["textContent"]


def attempted_nothing(attempted) -> bool:
    return attempted == []

"""Tests for vessel-related email filter (sync-time filtering).

Ensures disbursement account emails and maritime content pass the filter.
"""

from app.services.vessel_filter import is_vessel_related_email


def test_disbursement_proforma_email_passes():
    """Disbursement Account Proforma email should pass vessel filter (maritime keywords)."""
    subject = "Disbursement Account Proforma - MV Atlantic Star - Rotterdam NLRTM"
    body = """
    Dear Agent,
    Please find below the proforma Disbursement Account for MV Atlantic Star (IMO 9123456)
    port call at Rotterdam (NLRTM).
    ETA: 2025-03-15T06:00:00Z
    ETD: 2025-03-16T18:00:00Z
    Line items:
    - Pilotage: 1 x 1,850.00 USD = 1,850.00 USD
    - Port dues (per GRT): 12,500 GRT x 0.85 USD = 10,625.00 USD
    Total: 15,957.50 USD
    Best regards,
    Port Accounts
    """
    vessel_terms: list[tuple[str | None, str | None]] = []
    assert is_vessel_related_email(subject, body, None, vessel_terms) is True


def test_eta_etd_port_call_keywords_pass():
    """Emails with ETA, ETD, port call should pass heuristic."""
    body = "ETA: 2025-03-15. ETD: 2025-03-16. Port call at Rotterdam."
    assert is_vessel_related_email(None, body, None, []) is True


def test_disbursement_keyword_passes():
    """Email containing 'disbursement' should pass."""
    body = "Please find the disbursement account for your review."
    assert is_vessel_related_email(None, body, None, []) is True


def test_vessel_imo_keywords_pass():
    """Email with vessel and IMO should pass."""
    body = "Vessel MV Atlantic Star, IMO 9123456, arrival at berth."
    assert is_vessel_related_email(None, body, None, []) is True


def test_non_maritime_email_fails():
    """Generic non-maritime email should not pass."""
    subject = "Meeting tomorrow"
    body = "Hi, let's meet for coffee at 3pm. Thanks!"
    assert is_vessel_related_email(subject, body, None, []) is False


def test_vessel_terms_match_when_provided():
    """When tenant has vessels, match against vessel name/IMO."""
    vessel_terms = [("MV Atlantic Star", "9123456"), ("Pacific Voyager", None)]
    body = "Proforma for MV Atlantic Star at Rotterdam."
    assert is_vessel_related_email(None, body, None, vessel_terms) is True


def test_empty_content_fails():
    """Empty subject and body should not pass."""
    assert is_vessel_related_email("", "", None, []) is False
    assert is_vessel_related_email(None, None, None, []) is False

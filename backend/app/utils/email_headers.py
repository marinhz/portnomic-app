"""Decode MIME encoded-word headers (RFC 2047) for display."""

from email.header import decode_header


def decode_mime_header(value: str | None) -> str | None:
    """Decode RFC 2047 encoded-words (e.g. =?UTF-8?Q?Subject?=) to plain text.

    Gmail API and some IMAP providers return raw header values; this decodes them
    so subjects and sender names display correctly (e.g. em dashes, accented chars).
    """
    if not value or not isinstance(value, str):
        return value
    parts = decode_header(value)
    result: list[str] = []
    for part, charset in parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(str(part))
    return "".join(result)

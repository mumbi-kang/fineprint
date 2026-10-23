"""Checks that AI-quoted text really exists in the contract."""


def normalize(text: str) -> str:
    """Collapse all whitespace (spaces, tabs, line breaks) to single spaces."""
    return " ".join(text.split())


def quote_exists(quote: str, contract_text: str) -> bool:
    """Return True if quote appears in contract_text, ignoring differences in spacing/line breaks.
    An empty or whitespace-only quote is never valid."""
    clean_quote = normalize(quote)
    if not clean_quote:
        return False
    return clean_quote in normalize(contract_text)

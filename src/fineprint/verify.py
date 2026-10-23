"""Checks that AI-quoted text really exists in the contract."""


def quote_exists(quote: str, contract_text: str) -> bool:
    """Return True if quote appears in contract_text, ignoring differences in spacing/line breaks.
    An empty or whitespace-only quote is never valid."""
    clean_quote = " ".join(quote.split())          # normalize spacing in the AI's quote
    if not clean_quote:                            # empty or all-spaces quote = invalid
        return False
    clean_contract = " ".join(contract_text.split())  # normalize spacing in the contract
    return clean_quote in clean_contract           # is the quote really in the contract?

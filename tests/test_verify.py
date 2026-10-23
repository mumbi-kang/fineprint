from fineprint.verify import quote_exists

CONTRACT = "This Agreement renews for one year.\nIt is governed by   Delaware law."


def test_exact_match():
    assert quote_exists("renews for one year", CONTRACT)


def test_extra_spaces_and_line_breaks():
    assert quote_exists("renews  for\none year", CONTRACT)
    assert quote_exists("year. It is governed", CONTRACT)


def test_not_in_contract():
    assert not quote_exists("renews for two years", CONTRACT)


def test_empty_quote_is_invalid():
    assert not quote_exists("", CONTRACT)
    assert not quote_exists("   ", CONTRACT)
    
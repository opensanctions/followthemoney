from followthemoney.types import registry

emails = registry.email


def test_email_parse():
    # Cyrillic domain should be kept as is
    assert emails.clean("почта@орг.ру") == "почта@орг.ру"
    # Reject domain with a comma
    assert emails.clean("foo@pudo,org") is None
    # Domain with trailing dot should be stripped and valid
    assert emails.clean("foo@pudo.org.") == "foo@pudo.org"
    # Domain with a single-letter TLD (invalid)
    assert emails.clean("foo@pudo.o") is None

    assert emails.clean(" foo@pudo.org") == "foo@pudo.org"
    assert emails.clean("fo-o@pudo.org") == "fo-o@pudo.org"
    assert emails.clean("fo_o@pudo.org") == "fo_o@pudo.org"
    assert emails.clean("fo.o@pudo.org") == "fo.o@pudo.org"
    assert emails.clean("fo+o@pudo.org") == "fo+o@pudo.org"

    assert emails.clean("foo@pu do.org") is None
    # Local part with parentheses is invalid
    assert emails.clean("fo(o)@pudo.org") is None
    # Local part with a question mark is invalid
    assert emails.clean("foo?bar@pudo.org") is None
    # Local part with `mailto:` prefix
    assert emails.clean("mailto:foo@pudo.org") == "foo@pudo.org"
    # Email enclosed in angle brackets
    assert emails.clean("<mailto:foo@pudo.org>") is None
    assert emails.clean("<foo@pudo.org>") is None
    # Surrounding quotes
    assert emails.clean('   "foo@pudo.org"   ') is None
    assert emails.clean("foo@pudo.org") == "foo@pudo.org"
    assert emails.clean('"foo@pudo.org"') is None
    assert emails.clean("<foo@pudo.org>") is None
    assert emails.clean("pudo.org") is None
    assert emails.clean("@pudo.org") is None
    assert emails.clean("foo@") is None
    assert emails.clean(None) is None
    assert emails.clean("") is None
    assert emails.clean(5) is None
    assert emails.clean("foo@PUDO.org") == "foo@pudo.org"
    assert emails.clean("FOO@PUDO.org") == "FOO@pudo.org"
    long = "0123456789012345678901234567890123456789012345678901234567890"
    assert emails.clean(f"foo@{long}.example.com") == f"foo@{long}.example.com"
    # Too long domain part:
    assert emails.clean(f"foo@{long}567890123.example.com") is None

    assert emails.clean(f"{long}{long}@example.com") is None


def test_domain_validity():
    assert emails.validate("foo@pudo.org") is True
    assert emails.validate("foo@pudo") is False
    assert emails.validate("") is False
    assert emails.validate("@pudo.org") is False
    assert emails.validate("foo@") is False
    # Domain with Cyrillic-only TLD
    assert emails.validate("почта@орг.ру") is True
    # Domain with a single-character TLD
    assert emails.validate("foo@bar.c") is False
    # Domain with trailing dot
    assert emails.validate("foo@bar.org.") is True
    # Extra whitespace
    assert emails.validate("   foo@pudo.org   ") is True


def test_specificity():
    assert emails.specificity("foo@pudo.org") == 1

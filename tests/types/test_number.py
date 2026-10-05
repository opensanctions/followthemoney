from followthemoney.types import registry

numbers = registry.number


def test_cast_numbers():
    assert numbers.to_number("1,00,000") == 100000.0
    assert numbers.to_number(" -999.0") == -999.0
    assert numbers.to_number("- 1,00,000.234") == -100000.234
    assert numbers.to_number("99") == 99.0
    assert numbers.to_number("banana") is None
    assert numbers.to_number(None) is None


def test_parse_numbers():
    assert numbers.parse("99") == ("99", None)
    assert numbers.parse("1,00,000") == ("100000", None)
    assert numbers.parse(" -999.0") == ("-999.0", None)
    assert numbers.parse("- 1,00,000.234") == ("-100000.234", None)
    assert numbers.parse("banana") == (None, None)
    assert numbers.parse("5 kg") == ("5", "kg")
    assert numbers.parse("5kg") == ("5", "kg")
    assert numbers.parse("42 °C") == ("42", "°C")


def test_parse_numbers_no_silent_corruption():
    # Regression tests for issue #331: parse must not silently return a
    # structurally different number. Ambiguous or multi-number inputs should
    # yield (None, None) so callers can warn, rather than a plausible-but-wrong
    # value.

    # Space-grouped thousands must not truncate at the first space.
    assert numbers.parse("1 000 000") == ("1000000", None)

    # A European decimal comma under the default separator=',' is an invalid
    # thousands grouping (1-digit group) and must be rejected, not read as 15.
    assert numbers.parse("1,5") == (None, None)

    # Ranges must not collapse to the lower bound with '-' as the unit.
    assert numbers.parse("5,000,000 - 10,000,000") == (None, None)

    # European dot-grouping under the default decimal='.' is ambiguous and must
    # not be truncated with a garbage unit.
    assert numbers.parse("1.234.567") == (None, None)

    # Trailing content that is not a recognizable unit must be rejected rather
    # than the number silently taken from the head of the string.
    assert numbers.parse("12 and 34") == (None, None)


def test_parse_numbers_still_accepts_valid():
    # Guard against the stricter parser over-rejecting legitimate inputs.

    # Plain ungrouped integers of any length.
    assert numbers.parse("1000000") == ("1000000", None)
    assert numbers.parse("007") == ("007", None)

    # Western thousands grouping, with and without a decimal part.
    assert numbers.parse("1,000,000") == ("1000000", None)
    assert numbers.parse("1,000,000.50") == ("1000000.50", None)

    # Indian lakh/crore grouping.
    assert numbers.parse("1,00,00,000") == ("10000000", None)

    # Signs, including an explicit plus and a space after the sign.
    assert numbers.parse("+42") == ("+42", None)
    assert numbers.parse("- 999.0") == ("-999.0", None)

    # Decimals.
    assert numbers.parse("0.5") == ("0.5", None)

    # Surrounding whitespace is ignored.
    assert numbers.parse("  42  ") == ("42", None)

    # A variety of trailing units (letters, symbols, percent, degrees).
    assert numbers.parse("3.14 m") == ("3.14", "m")
    assert numbers.parse("100%") == ("100", "%")
    assert numbers.parse("10.5°C") == ("10.5", "°C")
    assert numbers.parse("1,234.5 kg") == ("1234.5", "kg")


def test_parse_numbers_rejects_digit_unit():
    # These exercise the digit-in-unit guard specifically: the pattern DOES
    # fully match, taking a leading number and a trailing "unit" that starts
    # with a non-digit but carries digits (e.g. "1.234" + ".567"). Such a unit
    # is really a second, glued-on number — a compact range, a repeated
    # decimal/grouping char, or an expression — so we reject rather than
    # return the head with a garbage unit. An exponent belongs to the number,
    # and the scientific-notation test covers it.
    assert numbers.parse("1.234.567") == (None, None)  # -> would be ("1.234", ".567")
    assert numbers.parse("1,5") == (None, None)  # -> would be ("1", ",5")
    assert numbers.parse("5-10") == (None, None)  # compact range
    assert numbers.parse("10-20kg") == (None, None)  # compact range with unit
    assert numbers.parse("3x4") == (None, None)
    assert numbers.parse("2+2") == (None, None)

    # A genuine unit with no digits is still accepted (the guard must not be
    # over-broad). Note "²" is not an ASCII decimal digit, so it survives.
    assert numbers.parse("5 m²") == ("5", "m²")
    assert numbers.parse("42°C") == ("42", "°C")


def test_parse_numbers_locale_config():
    # The inputs the default config rejects as ambiguous must parse correctly
    # once the caller supplies the right decimal/separator characters.
    assert numbers.parse("1,5", decimal=",", separator=".") == ("1.5", None)
    assert numbers.parse("1.234.567", decimal=",", separator=".") == (
        "1234567",
        None,
    )
    assert numbers.parse("1.234.567,89", decimal=",", separator=".") == (
        "1234567.89",
        None,
    )
    assert numbers.parse("1 234,56", decimal=",", separator=" ") == ("1234.56", None)
    assert numbers.parse("1.234,5 kg", decimal=",", separator=".") == ("1234.5", "kg")


def test_format_numbers():
    assert numbers.caption("100000") == "100,000"
    assert numbers.caption("-999.0") == "-999"
    assert numbers.caption("-100000.234") == "-100,000.23"
    assert numbers.caption("-100000.234tonnes") == "-100,000.23 tonnes"
    assert numbers.caption("banana") == "banana"
    assert numbers.caption("1,00,000") == "100,000"


def test_parse_numbers_infers_separator_from_both():
    # Issue #340.1: no convention mixes grouping characters, so a value holding
    # both reads one way, with the rightmost as the decimal. Nothing in the
    # codebase passes the decimal/separator arguments, so it is the only route.
    assert numbers.parse("1.000,00") == ("1000.00", None)
    assert numbers.parse("1.234.567,89") == ("1234567.89", None)
    assert numbers.parse("1.000,000") == ("1000.000", None)
    assert numbers.to_number("1.234.567,89") == 1234567.89

    # In western order the rightmost is the decimal too.
    assert numbers.parse("1,234,567.89") == ("1234567.89", None)

    # A unit comes back with the inferred number.
    assert numbers.parse("1.234,56 kg") == ("1234.56", "kg")

    # One separator alone stays ambiguous: "1,000" is a thousand under the
    # default grouping, and under lakh grouping two digits after it are not a
    # decimal either.
    assert numbers.parse("1,000") == ("1000", None)
    assert numbers.parse("1.000") == ("1.000", None)
    assert numbers.parse("12,34") == ("1234", None)

    # An explicit locale that disagrees with the inference is honoured,
    # because the inference only fires when both characters are present.
    assert numbers.parse("1,5", decimal=",", separator=".") == ("1.5", None)

    # A unit is part of the value and a grouping character inside one is no
    # locale signal, so the inference runs only where the given locale reads
    # nothing.
    assert numbers.parse("1.5 m,s") == ("1.5", "m,s")
    assert numbers.parse("10.5kg,m") == ("10.5", "kg,m")
    assert numbers.parse("1,5m.s", decimal=",", separator=".") == ("1.5", "m.s")


def test_parse_numbers_scientific_notation():
    # Issue #340.2: an exponent is unambiguous in every locale, so it belongs
    # to the number and not to the unit.
    assert numbers.parse("1e6") == ("1e6", None)
    assert numbers.to_number("1e6") == 1000000.0
    assert numbers.parse("1E5") == ("1E5", None)
    assert numbers.parse("1.5e-3") == ("1.5e-3", None)
    assert numbers.to_number("1.5e-3") == 0.0015
    assert numbers.parse("2.5E+4") == ("2.5E+4", None)
    assert numbers.parse("1e6 kg") == ("1e6", "kg")

    # A unit beginning with 'e' is not an exponent, and an 'e' with no digits
    # after it is not one either.
    assert numbers.parse("5eV") == ("5", "eV")
    assert numbers.parse("5 eV") == ("5", "eV")
    assert numbers.parse("1e") == ("1", "e")

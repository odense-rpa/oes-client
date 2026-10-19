"""Tests af fakturaer // Tests of debtor invoices.

soeg_fakturaer kun læser og kører mod ØS. De rene funktioner kræver ingen browser.
"""

from datetime import date

import pytest

from oes_client.fakturaer import parse_fakturarader, udtraek_cpr

OVERSKRIFT = [
    "",
    "Enummer",
    "Fakdato",
    "Faknr",
    "Restbel",
    "Forfdato",
    "Bilagstype",
    "Betart",
    "Institutionsnr",
]
SUMRAEKKE = ["", "", "", "", "", "", "0,00", "", "", "", ""]


def _raekke(
    cpr="0000000000",
    dato="12-03-2025",
    nr="1001",
    rest="1.250,50",
    forfald="11-04-2025",
    type_="Faktura",
):
    return ["", "", "", cpr, dato, nr, rest, forfald, type_, "258", "281"]


def test_udtraek_cpr():
    assert udtraek_cpr("999999-9999") == "9999999999"
    assert udtraek_cpr("9999999999") == "9999999999"
    assert udtraek_cpr("Cpr: 999999-9999.") == "9999999999"


@pytest.mark.parametrize("tekst", ["", "abc", "12345", "99999-99999", "99999999999"])
def test_udtraek_cpr_ugyldigt(tekst):
    with pytest.raises(ValueError):
        udtraek_cpr(tekst)


def test_parse_springer_overskrift_og_sumraekker_over():
    raekker = [OVERSKRIFT, SUMRAEKKE, _raekke(), _raekke(type_="Kreditnota", nr="1002")]
    fakturaer = parse_fakturarader(raekker)

    assert [f["fakturanr"] for f in fakturaer] == [1001, 1002]
    assert [f["type"] for f in fakturaer] == ["Faktura", "Kreditnota"]


def test_parse_felter():
    (faktura,) = parse_fakturarader([_raekke(cpr="000000-0000")])

    assert faktura == {
        "cpr": "0000000000",
        "faktura_dato": date(2025, 3, 12),
        "fakturanr": 1001,
        "rest_beloeb": 1250.5,
        "forfaldsdato": date(2025, 4, 11),
        "type": "Faktura",
        "art": "258",
        "institution": "281",
    }


def test_parse_tom_liste():
    assert parse_fakturarader([]) == []


def test_soeg_fakturaer_ugyldigt_cpr_foer_browser(oes):
    with pytest.raises(ValueError):
        oes.fakturaer.soeg_fakturaer("abc")


def test_soeg_fakturaer_ingen_fakturaer(oes):
    """Testpersonen i ØS test har ingen fakturaer."""
    assert oes.fakturaer.soeg_fakturaer("999999-9999") == []


def test_soeg_fakturaer_fundet(oes, test_faktura_cpr):
    fakturaer = oes.fakturaer.soeg_fakturaer(test_faktura_cpr)

    assert fakturaer
    assert {f["cpr"] for f in fakturaer} == {test_faktura_cpr.replace("-", "")}
    assert all(f["art"] == "258" for f in fakturaer)
    assert all(isinstance(f["faktura_dato"], date) for f in fakturaer)
    assert {f["type"] for f in fakturaer} <= {"Faktura", "Kreditnota"}

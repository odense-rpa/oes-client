"""Tests af fakturaer // Tests of debtor invoices.

soeg_fakturaer kun læser og kører mod ØS. De rene funktioner kræver ingen browser.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
from playwright.sync_api import TimeoutError

from oes_client import OESFejl
from oes_client.fakturaer import FakturaClient, parse_fakturarader, udtraek_cpr

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


# ------------------------------ opret_faktura (ingen browser) --------------------------


def _klient():
    klient = FakturaClient(MagicMock())
    klient._session.soeg_frame.return_value = None  # Rediger-knappen vises ikke endnu
    return klient


@pytest.mark.parametrize("varetekst", ["", "   ", "x" * 255])
def test_opret_faktura_ugyldig_varetekst_foer_browser(varetekst):
    klient = _klient()
    with pytest.raises(ValueError):
        klient.opret_faktura("999999-9999", varetekst)
    klient._session.naviger.assert_not_called()


def test_opret_faktura_ugyldigt_cpr_foer_browser():
    klient = _klient()
    with pytest.raises(ValueError):
        klient.opret_faktura("abc", "tekst")
    klient._session.naviger.assert_not_called()


def test_gem_lykkes_foerste_gang():
    klient = _klient()
    klient._session.vent_paa_en_af.return_value = (0, MagicMock())  # Rediger vises

    assert klient._gem(2) is True
    assert klient._session.klik.call_count == 1
    # der ventes på genindlæsning efter klikket, ikke på den gamle Gem-knap
    klient._session.vent_paa_genindlaesning.assert_called_once()


def test_gem_trykker_ikke_igen_hvis_forrige_klik_nåede_at_gemme():
    klient = _klient()
    klient._session.vent_paa_genindlaesning.side_effect = TimeoutError("langsom")
    klient._session.soeg_frame.return_value = MagicMock()  # Rediger vises nu

    assert klient._gem(2) is True
    assert klient._session.klik.call_count == 1


def test_gem_prover_igen_og_lykkes():
    klient = _klient()
    klient._session.vent_paa_en_af.side_effect = [(1, MagicMock()), (0, MagicMock())]

    assert klient._gem(2) is True
    assert klient._session.klik.call_count == 2


def test_gem_findes_allerede_giver_false():
    klient = _klient()
    klient._session.vent_paa_en_af.return_value = (1, MagicMock())  # Gem vises stadig
    klient._session.laes_fejlbeskeder.return_value = [
        "På institution 281 findes allerede en faktura for debitoren"
    ]

    assert klient._gem(2) is False
    assert klient._session.klik.call_count == 2


def test_gem_anden_fejl_giver_oesfejl_med_besked():
    klient = _klient()
    klient._session.vent_paa_en_af.return_value = (1, MagicMock())
    klient._session.laes_fejlbeskeder.return_value = ["Ugyldigt varenummer"]

    with pytest.raises(OESFejl, match="Ugyldigt varenummer"):
        klient._gem(2)


def test_gem_timeout_giver_oesfejl():
    klient = _klient()
    klient._session.vent_paa_en_af.side_effect = TimeoutError("ingen af")

    with pytest.raises(OESFejl, match="kunne ikke oprette"):
        klient._gem(2)

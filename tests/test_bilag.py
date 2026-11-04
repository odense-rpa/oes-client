"""Tests mod ØS Indsigt test (BASE_URL=https://odensetest.osi-local.dk/mod-core).

Tests der ændrer bilag kører kun med OES_ALLOW_WRITE=1.
"""

import os

import pytest

from oes_client.bilag import BILAG_KOLONNER, BilagIkkeFundet, _idag

skriv = pytest.mark.usefixtures("tillad_skriv")


def test_udsoeg_bilag(oes, test_afdelingsnummer):
    aar = _idag().year
    bilag = oes.bilag.udsoeg_bilag(
        regnskabsaar_fra=aar - 1,
        regnskabsaar_til=aar,
        afdelingsnummer=test_afdelingsnummer,
        bilagsdato_til=_idag(),
    )
    assert isinstance(bilag, list)
    for post in bilag:
        assert set(post) == set(BILAG_KOLONNER.values())
        assert post["Bilagsid"]


def test_hent_bilags_xml(oes, test_bilagsid):
    xml = oes.bilag.hent_bilags_xml(test_bilagsid)
    assert "Invoice" in xml
    assert len(oes.bilag.parse_konteringslinjer(xml)) > 0


def test_find_bilag_ukendt(oes):
    with pytest.raises(BilagIkkeFundet):
        oes.bilag.hent_bilags_xml("999999999999")


@skriv
def test_aendre_bemaerkning(oes, test_bilagsid):
    oes.bilag.aendre_bemaerkning(test_bilagsid, "Test af oes-client")

def _test_linjer(oes, bilagsid: str, kontonummer: str) -> list[dict]:
    """To linjer der summer til bilagets beløb inkl. moms."""
    # ØS kræver at linjerne summer til bilagets beløb inkl. moms
    # // ØS requires the lines to sum to the invoice total incl. moms
    xml = oes.bilag.hent_bilags_xml(bilagsid)
    total = round(
        sum(
            l["Amount"] + l["TaxAmount"] for l in oes.bilag.parse_konteringslinjer(xml)
        ),
        2,
    )
    cpr = os.getenv("TEST_CPR", "")
    return [
        {
            "Cpr": cpr,
            "Kontonummer": kontonummer,
            "Posteringstekst": "Test linje 1",
            "Beløb inkl moms": round(total + 25.5, 2),
        },
        {
            "Cpr": cpr,
            "Kontonummer": kontonummer,
            "Posteringstekst": "Test kredit",
            "Beløb inkl moms": -25.5,
        },
    ]


def _test_linjer_100(oes, bilagsid: str, kontonummer: str) -> list[dict]:
    """100 linjer der tilsammen summer til bilagets beløb inkl. moms."""
    xml = oes.bilag.hent_bilags_xml(bilagsid)
    # regnes i øre, så summen rammer præcist // computed in øre so the sum is exact
    total_oere = round(
        sum(
            l["Amount"] + l["TaxAmount"] for l in oes.bilag.parse_konteringslinjer(xml)
        )
        * 100
    )
    antal = 100
    beloeb_oere = [total_oere // antal] * antal
    # rest på sidste linje // remainder on the last line
    beloeb_oere[-1] += total_oere - sum(beloeb_oere)
    cpr = os.getenv("TEST_CPR", "")
    return [
        {
            "Cpr": cpr,
            "Kontonummer": kontonummer,
            "Posteringstekst": f"Test linje {n}",
            "Beløb inkl moms": oere / 100,
        }
        for n, oere in enumerate(beloeb_oere, start=1)
    ]


@skriv
def test_opret_konteringslinjer(oes):
    # bilaget skal have moms og en leverandør uden b-skat, og må ikke være varemodtaget.
    # Kan genbruges, da linjerne erstattes ved hver kørsel
    # // invoice needs moms, a supplier without b-skat, and must not be received
    bilagsid = os.getenv("TEST_BILAGSID")
    kontonummer = os.getenv("TEST_KONTONUMMER")
    if not bilagsid or not kontonummer:
        pytest.skip("TEST_KONTERING_BILAGSID eller TEST_KONTONUMMER er ikke sat")

    linjer = _test_linjer(oes, bilagsid, kontonummer)
    oes.bilag.opret_konteringslinjer(bilagsid, linjer, "Forberedt af test")


@skriv
def test_varemodtag_bilag(oes, test_bilagsid):
    oes.bilag.varemodtag_bilag(test_bilagsid, "Behandlet af test")




@skriv
def test_opret_konteringslinjer_og_varemodtag(oes):
    # varemodtagelse kan ikke gøres om, så bilaget kan kun bruges én gang
    # // receiving cannot be undone, so the invoice can only be used once
    kontonummer = os.getenv("TEST_KONTONUMMER")
    if not kontonummer:
        pytest.skip("TEST_KONTONUMMER er ikke sat")

    bilagsid = ""

    linjer = _test_linjer_100(oes, bilagsid, kontonummer)
    oes.bilag.opret_konteringslinjer(bilagsid, linjer, "Forberedt af test")
    # bilaget er stadig åbent, så varemodtag_bilag søger ikke igen
    # // invoice is still open, so varemodtag_bilag skips the search
    oes.bilag.varemodtag_bilag(bilagsid, "Behandlet af test")

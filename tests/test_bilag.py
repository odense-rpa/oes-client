"""Tests mod ØS Indsigt test (BASE_URL=https://odensetest.osi-local.dk/mod-core).

Tests der ændrer bilag kører kun med OES_ALLOW_WRITE=1.
"""

import os

import pytest

from oes_client.bilag import BILAG_KOLONNER, BilagIkkeFundet, _idag

skriv = pytest.mark.skipif(
    os.getenv("OES_ALLOW_WRITE") != "1",
    reason="ændrer bilag i ØS - sæt OES_ALLOW_WRITE=1",
)


def test_udsoeg_bilag(oes_bilag_client, test_afdelingsnummer):
    aar = _idag().year
    bilag = oes_bilag_client.udsoeg_bilag(
        regnskabsaar_fra=aar - 1,
        regnskabsaar_til=aar,
        afdelingsnummer=test_afdelingsnummer,
        bilagsdato_til=_idag(),
    )
    assert isinstance(bilag, list)
    for post in bilag:
        assert set(post) == set(BILAG_KOLONNER.values())
        assert post["Bilagsid"]


def test_hent_bilags_xml(oes_bilag_client, test_bilagsid):
    xml = oes_bilag_client.hent_bilags_xml(test_bilagsid)
    assert "Invoice" in xml
    assert len(oes_bilag_client.parse_konteringslinjer(xml)) > 0


def test_find_bilag_ukendt(oes_bilag_client):
    with pytest.raises(BilagIkkeFundet):
        oes_bilag_client.hent_bilags_xml("999999999999")


@skriv
def test_aendre_bemaerkning(oes_bilag_client, test_bilagsid):
    oes_bilag_client.aendre_bemaerkning(test_bilagsid, "Test af oes-client")


@skriv
def test_opret_konteringslinjer(oes_bilag_client):
    # bilaget skal have moms og en leverandør uden b-skat, og må ikke være varemodtaget.
    # Kan genbruges, da linjerne erstattes ved hver kørsel
    # // invoice needs moms, a supplier without b-skat, and must not be received
    bilagsid = os.getenv("TEST_KONTERING_BILAGSID")
    kontonummer = os.getenv("TEST_KONTONUMMER")
    if not bilagsid or not kontonummer:
        pytest.skip("TEST_KONTERING_BILAGSID eller TEST_KONTONUMMER er ikke sat")

    # ØS kræver at linjerne summer til bilagets beløb inkl. moms
    # // ØS requires the lines to sum to the invoice total incl. moms
    xml = oes_bilag_client.hent_bilags_xml(bilagsid)
    total = round(
        sum(
            l["Amount"] + l["TaxAmount"]
            for l in oes_bilag_client.parse_konteringslinjer(xml)
        ),
        2,
    )
    cpr = os.getenv("TEST_CPR", "")
    linjer = [
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
    oes_bilag_client.opret_konteringslinjer(bilagsid, linjer, "Forberedt af test")


@skriv
def test_varemodtag_bilag(oes_bilag_client, test_bilagsid):
    oes_bilag_client.varemodtag_bilag(
        test_bilagsid,
        cpr=os.getenv("TEST_CPR", ""),
        kontonummer=os.getenv("TEST_KONTONUMMER", ""),
        posteringstekst="Test",
        bemaerkning="Behandlet af test",
    )


@skriv
def test_varemodtag_bilag_konteret(oes_bilag_client, test_bilagsid):
    oes_bilag_client.varemodtag_bilag_konteret(test_bilagsid, "Behandlet af test")

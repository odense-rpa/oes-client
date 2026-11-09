from pathlib import Path

from oes_client.bilag_xml import parse_konteringslinjer

XML = (Path(__file__).parent / "fixtures" / "eksempel_faktura.xml").read_text(
    encoding="utf-8"
)


def test_parse_konteringslinjer():
    linjer = parse_konteringslinjer(XML)

    assert len(linjer) == 2
    foerste, anden = linjer

    assert foerste["Id"] == "1"
    assert foerste["Amount"] == 1234.50
    assert foerste["Name"] == "Rollator model X"
    assert foerste["Description"] == "Rollator"
    assert foerste["Note"] == "Borger 010101-1234"
    assert foerste["DeliveryParty"].strip() == "0101011234"
    # samlet tekst for hele undertræet, som i Blue Prism // concatenated subtree text
    assert "Jens Hansen" in foerste["PartyLegalEntity"]
    assert "0101011234" in foerste["PartyLegalEntity"]
    assert foerste["TaxAmount"] == 308.63

    assert anden["Amount"] == -100.0
    assert anden["Description"] == ""
    assert anden["Note"] == ""
    assert anden["DeliveryParty"] == ""
    assert anden["TaxAmount"] == 0.0


def test_parse_konteringslinjer_uden_namespace_og_med_bom():
    xml = "﻿<invoice><invoiceline><id>7</id><lineextensionamount>5</lineextensionamount></invoiceline></invoice>"
    assert parse_konteringslinjer(xml)[0]["Amount"] == 5.0


def _faktura(beloeb: str, momser: list[str], procent: str | None = "25") -> str:
    """Syntetisk OIOUBL-faktura med én linje og en TaxTotal pr. moms.
    // Synthetic OIOUBL invoice with one line and one TaxTotal per VAT amount."""
    kategori = (
        f"<cac:TaxCategory><cbc:Percent>{procent}</cbc:Percent></cac:TaxCategory>"
        if procent is not None
        else ""
    )
    totaler = "".join(
        f"<cac:TaxTotal>"
        f'<cbc:TaxAmount currencyID="DKK">{moms}</cbc:TaxAmount>'
        f"<cac:TaxSubtotal>"
        f'<cbc:TaxAmount currencyID="DKK">{moms}</cbc:TaxAmount>'
        f"{kategori}"
        f"</cac:TaxSubtotal>"
        f"</cac:TaxTotal>"
        for moms in momser
    )
    return (
        '<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"'
        ' xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"'
        ' xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">'
        "<cac:InvoiceLine>"
        "<cbc:ID>1</cbc:ID>"
        f'<cbc:LineExtensionAmount currencyID="DKK">{beloeb}</cbc:LineExtensionAmount>'
        f"{totaler}"
        "<cac:Item><cbc:Name>Testvare</cbc:Name></cac:Item>"
        "</cac:InvoiceLine>"
        "</Invoice>"
    )


def _moms(xml: str) -> float:
    return parse_konteringslinjer(xml)[0]["TaxAmount"]


def test_moms_en_taxtotal_uaendret():
    assert _moms(_faktura("100.00", ["25.00"])) == 25.0


def test_moms_to_taxtotal_vaelger_den_rigtige():
    # den første TaxTotal har et lille beløb, den anden den rigtige moms
    # // the first TaxTotal holds a small amount, the second the real VAT
    assert _moms(_faktura("29.91", ["0.01", "7.48"])) == 7.48


def test_moms_to_taxtotal_stort_antal():
    assert _moms(_faktura("477.28", ["1.45", "119.32"])) == 119.32


def test_moms_to_taxtotal_omvendt_raekkefoelge():
    assert _moms(_faktura("29.91", ["7.48", "0.01"])) == 7.48


def test_moms_ingen_taxtotal():
    moms = _moms(_faktura("100.00", []))
    assert moms == 0.0
    assert isinstance(moms, float)


def test_moms_flere_taxtotal_uden_procent():
    # uden procent kan den rigtige ikke udpeges - første TaxAmount som før
    # // without a percent the real one can't be identified - first TaxAmount as before
    assert _moms(_faktura("29.91", ["0.01", "7.48"], procent=None)) == 0.01

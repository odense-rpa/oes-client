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

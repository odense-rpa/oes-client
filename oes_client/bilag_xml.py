"""Parsing af bilags-XML (OIOUBL) // Parsing of invoice XML (OIOUBL).

Port af Blue Prism handlingen "Hent konteringslinjer fra bilags-xml".
"""

import xml.etree.ElementTree as ET


def _localname(element: ET.Element) -> str:
    # fjerner namespace og ignorerer store/små bogstaver // strip namespace, ignore case
    return element.tag.rsplit("}", 1)[-1].lower()


def _foerste(element: ET.Element | None, navn: str) -> ET.Element | None:
    # første efterkommer (ikke kun direkte barn) med givent navn
    # // first descendant (not only direct child) with the given name
    if element is None:
        return None
    for e in element.iter():
        if e is not element and _localname(e) == navn:
            return e
    return None


def _boern(element: ET.Element, navn: str) -> list[ET.Element]:
    # direkte børn (ikke efterkommere) med givent navn
    # // direct children (not descendants) with the given name
    return [e for e in element if _localname(e) == navn]


def _tekst(element: ET.Element | None) -> str:
    # samlet tekst for hele undertræet, som .Value i C#
    # // concatenated text of the whole subtree, like .Value in C#
    return "".join(element.itertext()) if element is not None else ""


def _tal(element: ET.Element | None) -> float:
    tekst = _tekst(element).strip()
    return float(tekst) if tekst else 0.0


def _momsbeloeb(line: ET.Element) -> float:
    """Linjens moms. Har linjen flere TaxTotal, vælges det TaxAmount der ligger
    tættest på LineExtensionAmount * Percent / 100. Ellers som før: første
    TaxAmount i linjen, eller 0.0.
    // The line's VAT. With several TaxTotals, pick the TaxAmount closest to
    LineExtensionAmount * Percent / 100. Otherwise as before.
    """
    # TaxAmount direkte under hver TaxTotal - ikke TaxSubtotal'ens
    # // TaxAmount directly under each TaxTotal - not the TaxSubtotal's
    kandidater = [
        _tal(beloeb)
        for total in _boern(line, "taxtotal")
        for beloeb in _boern(total, "taxamount")[:1]
    ]
    procent = _foerste(line, "percent")
    if len(kandidater) > 1 and _tekst(procent).strip():
        forventet = _tal(_foerste(line, "lineextensionamount")) * _tal(procent) / 100
        return min(kandidater, key=lambda b: abs(b - forventet))
    return _tal(_foerste(line, "taxamount"))


def parse_konteringslinjer(xml: str) -> list[dict]:
    """Returnerer én dict pr. InvoiceLine i bilags-XML'en.

    Nøgler: Id, Amount, Name, Description, Note, DeliveryParty, PartyLegalEntity,
    TaxAmount. Beløb er med decimalpunktum i XML'en.
    TaxAmount: se _momsbeloeb (linjer med flere TaxTotal).
    """
    root = ET.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml)
    linjer = []
    for line in (e for e in root.iter() if _localname(e) == "invoiceline"):
        item = _foerste(line, "item")
        deliveryparty = _foerste(_foerste(line, "delivery"), "deliveryparty")
        linjer.append(
            {
                "Id": _tekst(_foerste(line, "id")),
                "Amount": _tal(_foerste(line, "lineextensionamount")),
                "Name": _tekst(_foerste(item, "name")),
                "Description": _tekst(_foerste(item, "description")),
                # note læses i hele linjen, men kun hvis der er et item (som i Blue Prism)
                # // note is read from the whole line, but only if an item exists
                "Note": _tekst(_foerste(line, "note")) if item is not None else "",
                "DeliveryParty": _tekst(_foerste(deliveryparty, "partyidentification")),
                "PartyLegalEntity": _tekst(_foerste(deliveryparty, "partylegalentity")),
                "TaxAmount": _momsbeloeb(line),
            }
        )
    return linjer

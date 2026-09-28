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


def _tekst(element: ET.Element | None) -> str:
    # samlet tekst for hele undertræet, som .Value i C#
    # // concatenated text of the whole subtree, like .Value in C#
    return "".join(element.itertext()) if element is not None else ""


def _tal(element: ET.Element | None) -> float:
    tekst = _tekst(element).strip()
    return float(tekst) if tekst else 0.0


def parse_konteringslinjer(xml: str) -> list[dict]:
    """Returnerer én dict pr. InvoiceLine i bilags-XML'en.

    Nøgler: Id, Amount, Name, Description, Note, DeliveryParty, PartyLegalEntity,
    TaxAmount. Beløb er med decimalpunktum i XML'en.
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
                "TaxAmount": _tal(_foerste(line, "taxamount")),
            }
        )
    return linjer

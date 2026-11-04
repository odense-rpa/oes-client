"""Bilagshåndtering i ØS Indsigt // Invoice handling in ØS Indsigt.

Port af handlingerne fra Blue Prism objektet "ØS Indsigt (Chrome) VBO", som bruges af
processerne "Betaling af hjælpemiddelregninger v2" og "Lægeerklæringer - Betaling af
statusattester".
"""

import re
from datetime import date, datetime
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from playwright.sync_api import Frame, Locator, TimeoutError

from .bilag_xml import parse_konteringslinjer
from .exceptions import BilagIkkeFundet, OESFejl
from .selectors import BilagFrames as bf
from .selectors import BilagSelectors as bs
from .session import INGEN_RESULTATER, OESSession

__all__ = ["BilagClient", "BilagIkkeFundet", "OESFejl", "parse_konteringslinjer"]

# kolonner i resultattabellen på bilagsoversigten (0-indekseret)
# // columns in the result table of the invoice overview (0-indexed)
BILAG_KOLONNER = {
    3: "Bilagsid",
    4: "Bilagsart",
    5: "Status",
    6: "Bemærkning",
    7: "Betaling-leveringsdato",
    8: "Beløb inkl moms",
    9: "Beløb eks moms",
    10: "Leverandørnummer",
    11: "Leverandørnavn",
    12: "Cpr",
    13: "Afdelingsnummer",
    14: "Faktura-bestildato",
    15: "Regnskabsår",
    16: "Oprettet",
}
DATO_KOLONNER = {"Betaling-leveringsdato", "Faktura-bestildato", "Oprettet"}
TAL_KOLONNER = {"Beløb inkl moms", "Beløb eks moms"}


def _dansk_tal(tekst: str) -> float | None:
    tekst = tekst.strip().replace(".", "").replace(",", ".")
    try:
        return float(tekst)
    except ValueError:
        return None


def _dansk_dato(tekst: str) -> date | None:
    # dd-mm-yyyy, dd.mm.yyyy, dd/mm/yyyy eller med 2-cifret år // or with 2-digit year
    match = re.fullmatch(r"(\d{1,2})[-./](\d{1,2})[-./](\d{2}|\d{4})", tekst.strip())
    if not match:
        return None
    dag, maaned, aar = (int(x) for x in match.groups())
    try:
        return date(aar + 2000 if aar < 100 else aar, maaned, dag)
    except ValueError:
        return None


def _idag() -> date:
    return datetime.now(ZoneInfo("Europe/Copenhagen")).date()


def _dansk_beloeb(beloeb: float) -> str:
    return f"{beloeb:.2f}".replace(".", ",")


class BilagClient:
    """Bilagshandlinger i ØS Indsigt // Invoice actions in ØS Indsigt.

    Oprettes af OESClient og tilgås som oes.bilag.
    """

    parse_konteringslinjer = staticmethod(parse_konteringslinjer)

    def __init__(self, session: OESSession):
        self._session = session

    # ------------------------------ Hjælpere // Helpers -------------------------------

    def _bilagsoversigt(self) -> Frame:
        self._session.naviger("bilag/oversigt")
        return self._session.frame_med(bs.BILAGSOVERSIGT_OVERSKRIFT, bf.BILAGSOVERSIGT)

    def _laes_fejlbeskeder(self) -> list[str]:
        try:
            frame = self._session.frame_med(bs.FEJLLISTE, timeout=5_000)
        except TimeoutError:
            return []
        tekster = frame.locator(bs.FEJLLISTE).first.locator("option").all_inner_texts()
        return [t.strip() for t in tekster if t.strip()]

    def _find_bilag(self, bilagsid: str, rediger: bool = False, **status: bool) -> bool:
        """Fremsøger et bilag på bident og åbner det. Returnerer False hvis ikke fundet.

        status: ubehandlet, behandles, foranvises, konteret, bogfoeres, efteranvises,
        bogfoert, sendte, kladde, varemodtaget, inaktiveret. Alle er False som
        standard undtagen kladde, ubehandlet og varemodtaget.
        """
        ukendte = set(status) - set(bs.STATUS_CHECKBOXE)
        if ukendte:
            raise ValueError(f"Ukendte statusfelter: {ukendte}")

        frame = self._bilagsoversigt()
        frame.locator(bs.AFDELINGSNR_FRA).fill("")
        frame.locator(bs.SOEGNINGSTYPE).select_option(label="Bident")
        frame.locator(bs.BIDENT).fill(bilagsid)

        # i januar og februar søges også i sidste års regnskab
        # // in January and February, also search last year's accounts
        idag = _idag()
        if idag.month in (1, 2):
            frame.locator(bs.REGNSKABSAAR_FRA).select_option(label=str(idag.year - 1))

        for navn, selector in bs.STATUS_CHECKBOXE.items():
            frame.locator(selector).set_checked(
                status.get(navn, navn in ("kladde", "ubehandlet", "varemodtaget"))
            )

        self._session.klik(bs.VIS_KNAP, bf.BILAGSOVERSIGT_BTM)
        self._session.vent_paa_loading()

        try:
            self._session.frame_med(
                bs.BILAGSIDENTIFIKATION,
                bf.EBILAG,
                timeout=15_000,
                has_text=re.compile(rf"^\s*{re.escape(bilagsid)}"),
            )
        except TimeoutError:
            fejl = " ".join(self._session.laes_fejlbeskeder())
            if "Der var ingen Bilag" in fejl and INGEN_RESULTATER in fejl:
                return False
            raise TimeoutError(f"Bilagsidentifikation kunne ikke findes. {fejl}")

        if rediger:
            self._rediger()
        return True

    def _rediger(self) -> None:
        self._session.klik(bs.REDIGER_KNAP, bf.EBILAG_BTM)
        try:
            self._session.frame_med(bs.GEM_KNAP, bf.EBILAG_BTM, timeout=30_000)
        except TimeoutError:
            fejl = " ".join(self._session.laes_fejlbeskeder())
            raise TimeoutError(
                f"ØS åbnede ikke bilaget til redigering. {fejl}".strip()
            ) from None
        self._session.vent_paa_loading()

    def _bilag_er_aabent(self, bilagsid: str) -> bool:
        """Om bilaget allerede er åbent i ØS // Whether the invoice is already open."""
        return (
            self._session.soeg_frame(
                bs.BILAGSIDENTIFIKATION,
                bf.EBILAG,
                has_text=re.compile(rf"^\s*{re.escape(bilagsid)}\b"),
            )
            is not None
        )

    def _aabn_til_redigering(self, bilagsid: str, **status: bool) -> Frame:
        if not self._find_bilag(bilagsid, rediger=True, **status):
            raise BilagIkkeFundet(f"Fandt ikke bilag {bilagsid}")
        return self._session.frame_med(bs.BEMAERKNING, bf.EBILAG)

    def _gem(self, forventet_knap: str) -> None:
        """Trykker Gem og venter på at forventet_knap (fx Rediger) eller ØS' besked
        "E-bilag gemt" kommer frem."""
        # indeks 0 og 1 = gemt, 2 = Gem vises igen (afvist)
        # // index 0 and 1 = saved, 2 = Gem shown again (refused)
        muligheder = [
            (forventet_knap, bf.EBILAG_BTM),
            (bs.GEMT_BESKED, None),
            (bs.GEM_KNAP, bf.EBILAG_BTM),
        ]
        for forsoeg in range(3):
            if forsoeg:
                # den forrige Gem kan stadig være i gang - vent på resultatet før der
                # trykkes igen // the previous Gem may still be running - wait for its
                # result before retrying
                try:
                    i, _ = self._session.vent_paa_en_af(muligheder, 30_000)
                except TimeoutError:
                    break
                if i in (0, 1):
                    return  # den forrige Gem nåede at gemme // the previous Gem saved
            gem = (
                self._session.frame_med(bs.GEM_KNAP, bf.EBILAG_BTM)
                .locator(bs.GEM_KNAP)
                .first
            )
            try:
                self._session.klik_og_vent_paa_genindlaesning(gem, 30_000)
            except TimeoutError:
                continue
            self._session.vent_paa_loading()
            try:
                i, _ = self._session.vent_paa_en_af(muligheder, 10_000)
            except TimeoutError:
                continue
            if i in (0, 1):
                return
        fejl = "\n".join(self._session.laes_fejlbeskeder())
        raise OESFejl(f"Fejl kunne ikke gemme\n{fejl}")

    def _varemodtag(self) -> None:
        knap = self._session.klik(bs.VAREMODTAG_KNAP, bf.EBILAG_BTM)
        try:
            knap.wait_for(state="hidden", timeout=10_000)
        except TimeoutError:
            raise TimeoutError("Fejl ved tryk på varemodtag") from None

    @staticmethod
    def _saet_b_skat(felt: Locator, b_skat: str) -> None:
        """Vælger b-skat ud fra teksten, fx "1: B-skat m/AM-bidrag". Tom = ingen."""
        valgt = felt.evaluate("s => s.options[s.selectedIndex]?.text ?? ''")
        if valgt.strip() == b_skat.strip():
            return
        if b_skat.strip():
            felt.select_option(label=b_skat)
        else:
            felt.select_option(index=0)  # tom b-skat // blank b-skat

    def _laes_tabel(self) -> list[list[str]]:
        return self._session.laes_resultattabel_side()

    def _hent_tabel(self) -> list[list[str]]:
        """Læser alle sider af resultatlisten // Reads all pages of the result list."""
        return self._session.hent_resultattabel()

    # ------------------------------ Handlinger // Actions -----------------------------

    def udsoeg_bilag(
        self,
        regnskabsaar_fra: int,
        regnskabsaar_til: int,
        afdelingsnummer: str,
        bilagsdato_fra: date | None = None,
        bilagsdato_til: date | None = None,
        maks_beloeb: float | None = None,
        cpr: str = "",
        ubehandlet: bool = True,
        behandles: bool = False,
        foranvises: bool = False,
        konteret: bool = False,
        bogfoeres: bool = False,
        efteranvises: bool = False,
        bogfoert: bool = False,
        sendte: bool = False,
        kladde: bool = True,
        varemodtaget: bool = False,
        inaktiveret: bool = False,
    ) -> list[dict]:
        """Søger bilag på bilagsoversigten. Datoerne filtrerer på oprettet dato.

        Statusparametrene sætter bilagsstatus-checkboxene; kun ubehandlet og kladde
        er True som standard.
        """
        if not afdelingsnummer or not regnskabsaar_fra or not regnskabsaar_til:
            raise ValueError(
                "Der skal som minimum angives regnskabsår til og fra samt afdelingsnummer"
            )

        frame = self._bilagsoversigt()
        frame.locator(bs.REGNSKABSAAR_TIL).select_option(label=str(regnskabsaar_til))
        frame.locator(bs.REGNSKABSAAR_FRA).select_option(label=str(regnskabsaar_fra))
        frame.locator(bs.AFDELINGSNR_TIL).fill(afdelingsnummer)
        frame.locator(bs.AFDELINGSNR_FRA).fill(afdelingsnummer)
        # cpr-felterne ligger på en skjult fane, så værdien sættes direkte
        # // cpr fields are on a hidden tab, so set the value directly
        for selector in (bs.CPRNR_FRA, bs.CPRNR_TIL):
            frame.locator(selector).evaluate("(e, v) => e.value = v", cpr)
        frame.locator(bs.DATO_TYPE).select_option(label="Oprettet dato")
        if maks_beloeb is not None:
            frame.locator(bs.BELOEB_TIL).fill(_dansk_beloeb(maks_beloeb))
        for selector, dato in (
            (bs.DATO_FRA, bilagsdato_fra),
            (bs.DATO_TIL, bilagsdato_til),
        ):
            frame.locator(selector).fill(dato.strftime("%d%m%Y") if dato else "")
        status = {
            "ubehandlet": ubehandlet,
            "behandles": behandles,
            "foranvises": foranvises,
            "konteret": konteret,
            "bogfoeres": bogfoeres,
            "efteranvises": efteranvises,
            "bogfoert": bogfoert,
            "sendte": sendte,
            "kladde": kladde,
            "varemodtaget": varemodtaget,
            "inaktiveret": inaktiveret,
        }
        for navn, selector in bs.STATUS_CHECKBOXE.items():
            frame.locator(selector).set_checked(status[navn])

        self._session.klik(bs.VIS_KNAP, bf.BILAGSOVERSIGT_BTM)
        self._session.vent_paa_loading()

        # ved kun ét resultat åbner ØS bilaget direkte - gå tilbage til listen
        # // with a single hit ØS opens the invoice directly - go back to the list
        try:
            i, _ = self._session.vent_paa_en_af(
                [
                    (bs.FAKTURA_DETALJER_OVERSKRIFT, bf.EBILAG),
                    (bs.SIDETALSVAELGER, None),
                    (bs.FEJLLISTE, None),
                ],
                10_000,
            )
            if i == 0:
                self._session.klik(bs.TILBAGE_KNAP, bf.BTM)
                self._session.vent_paa_loading()
        except TimeoutError:
            pass

        bilag = []
        for raekke in self._hent_tabel():
            # header- og sumrækker frasorteres // skip header and total rows
            if len(raekke) <= max(BILAG_KOLONNER) or _dansk_tal(raekke[3]) is None:
                continue
            post = {}
            for indeks, navn in BILAG_KOLONNER.items():
                vaerdi = raekke[indeks].strip()
                if navn in DATO_KOLONNER:
                    post[navn] = _dansk_dato(vaerdi)
                elif navn in TAL_KOLONNER:
                    post[navn] = _dansk_tal(vaerdi)
                elif navn == "Regnskabsår":
                    post[navn] = int(vaerdi) if vaerdi.isdigit() else None
                elif navn == "Cpr":
                    post[navn] = vaerdi.replace("-", "")
                else:
                    post[navn] = vaerdi
            bilag.append(post)
        return bilag

    def hent_bilags_xml(self, bilagsid: str) -> str:
        """Henter den originale faktura-XML (OIOUBL) for et bilag."""
        # kun læsning, så der søges i alle statusser // read-only, search all statuses
        alle_status = dict.fromkeys(bs.STATUS_CHECKBOXE, True)
        if not self._find_bilag(bilagsid, **alle_status):
            raise BilagIkkeFundet(f"Fandt ikke bilag {bilagsid}")

        self._session.klik(bs.ORIGINAL_FANE, bf.EBILAG)
        try:
            frame = self._session.frame_med(
                bs.XML_LINK, bf.ORIGINAL_XML, timeout=10_000
            )
        except TimeoutError:
            raise TimeoutError("Kunne ikke finde link til xml fil") from None
        href = frame.locator(bs.XML_LINK).first.get_attribute("href")

        # hentes via browserens session, så cookies følger med
        # // fetched through the browser session so cookies are included
        svar = self._session.context.request.get(urljoin(frame.url, href))
        if not svar.ok:
            raise OESFejl(f"Kunne ikke hente xml ({svar.status}): {href}")
        return svar.text()

    def opret_konteringslinjer(self, bilagsid: str, linjer: list[dict], bemaerkning: str = "") -> None:
        """Erstatter bilagets konteringslinjer og gemmer.

        linjer: dicts med nøglerne Cpr, Kontonummer, Posteringstekst, Beløb inkl moms
        og evt. B-skat. B-skat angives som teksten i listen, fx "1: B-skat m/AM-bidrag";
        "" fjerner b-skat, og uden nøglen beholdes ØS' forslag. Summen af linjerne skal
        svare til bilagets beløb, ellers afviser ØS at gemme.
        Højst 1000 linjer, både i linjer og på bilagets eksisterende konteringslinjer;
        ellers rejses ValueError.
        """
        # behandles medtages, så et bilag med gemte linjer også findes ved genkørsel
        # // include behandles so an invoice with saved lines is found on retry
        self._aabn_til_redigering(bilagsid, bogfoeres=True, behandles=True)

        # slet alle linjer undtagen den første. Kun række 0 har inputfelter, de øvrige
        # er skrivebeskyttede, så der slettes nedefra
        # // delete all lines but the first; only row 0 is editable, so delete from
        # the bottom

        max_linjer = 1000

        if len(linjer) > max_linjer:
            raise ValueError("For mange konteringslinjer der skal oprettes til vi kan håndtere det")

        frame = self._session.frame_med(
                        bs.BIDENT_LINJE.format(n=0), bf.EBILAG, 60_000
                    )

        raekker = frame.eval_on_selector_all(
                        bs.SLET_LINJER,
                        "as => as.map(a => +a.getAttribute('href').match(/_LKF_,(\\d+)/)[1])",
                    )

        linjer_til_slet = len(raekker)

        if linjer_til_slet > max_linjer:
            raise ValueError("For mange linjer der skal slettes på den eksisterende regning")

        for _ in range(linjer_til_slet+1):
            frame = self._session.frame_med(
                bs.BIDENT_LINJE.format(n=0), bf.EBILAG, 60_000
            )
            raekker = frame.eval_on_selector_all(
                bs.SLET_LINJER,
                "as => as.map(a => +a.getAttribute('href').match(/_LKF_,(\\d+)/)[1])",
            )
            sidste = max(raekker, default=0)
            if sidste == 0:
                break
            self._session.klik_og_vent_paa_genindlaesning(
                frame.locator(bs.SLET_LINJE.format(n=sidste)).first,
                60_000,
                anker=frame.locator(bs.BIDENT_LINJE.format(n=0)),
            )
        else:
            raise OESFejl("Fejl ved sletning af rækker")

        for n, linje in enumerate(linjer):
            frame = self._session.frame_med(
                bs.BIDENT_LINJE.format(n=n), bf.EBILAG, 60_000
            )
            beloeb = float(linje["Beløb inkl moms"])
            frame.locator(bs.BIDENT_LINJE.format(n=n)).fill(bilagsid)
            frame.locator(bs.CPR_LINJE.format(n=n)).fill(linje["Cpr"])
            frame.locator(bs.KONTONR_LINJE.format(n=n)).fill(linje["Kontonummer"])
            frame.locator(bs.POSTERINGSTEKST_LINJE.format(n=n)).fill(
                linje["Posteringstekst"][:39]
            )
            frame.locator(bs.BELOEB_LINJE.format(n=n)).fill(_dansk_beloeb(abs(beloeb)))
            frame.locator(bs.DEBET_KREDIT_LINJE.format(n=n)).select_option(
                label="K" if beloeb < 0 else "D"
            )
            if "B-skat" in linje:
                self._saet_b_skat(
                    frame.locator(bs.B_SKAT_LINJE.format(n=n)), linje["B-skat"]
                )

            if n < len(linjer) - 1:
                # tilføj efter sidste række, så nye linjer kommer sidst. ØS validerer
                # linjerne ved tilføj og tilføjer ikke rækken ved fejl. Tidligere
                # rækker bliver skrivebeskyttede, så kun den aktuelle række har felter
                # // add after the last row; ØS validates and refuses on errors.
                # Earlier rows become read-only, so only the current row has inputs
                self._session.klik_og_vent_paa_genindlaesning(
                    frame.locator(bs.TILFOEJ_LINJE.format(n=n)).first,
                    60_000,
                    anker=frame.locator(bs.BIDENT_LINJE.format(n=n)),
                )
                # ny række = tilføjet; aktuel række stadig redigerbar = afvist af ØS
                # // new row = added; current row still editable = refused by ØS
                i, _ = self._session.vent_paa_en_af(
                    [
                        (bs.BIDENT_LINJE.format(n=n + 1), bf.EBILAG),
                        (bs.BIDENT_LINJE.format(n=n), bf.EBILAG),
                    ],
                    60_000,
                )
                if i == 1:
                    fejl = "\n".join(self._session.laes_fejlbeskeder())
                    raise OESFejl(f"Kunne ikke tilføje konteringslinje\n{fejl}")

        if bemaerkning:
            self._session.frame_med(bs.BEMAERKNING, bf.EBILAG).locator(
                bs.BEMAERKNING
            ).fill(bemaerkning)
        self._gem(bs.REDIGER_KNAP)

    def varemodtag_bilag(self, bilagsid: str, bemaerkning: str = "") -> None:
        """Skriver evt. bemærkning, gemmer og varemodtager bilaget.

        Opretter ikke konteringslinjer - brug opret_konteringslinjer først. Er bilaget
        allerede åbent (fx lige efter opret_konteringslinjer), bruges det uden ny søgning.
        """
        if self._bilag_er_aabent(bilagsid):
            # bilaget er allerede åbent (fx efter opret_konteringslinjer) - spring
            # søgning over // invoice already open (e.g. after opret_konteringslinjer)
            # - skip the search
            if self._session.soeg_frame(bs.GEM_KNAP, bf.EBILAG_BTM) is None:
                self._rediger()
            frame = self._session.frame_med(bs.BEMAERKNING, bf.EBILAG)
        else:
            frame = self._aabn_til_redigering(
                bilagsid, behandles=True, konteret=True, bogfoeres=True
            )
        if bemaerkning:
            frame.locator(bs.BEMAERKNING).fill(bemaerkning[:60])
        self._gem(bs.VAREMODTAG_KNAP)
        self._varemodtag()

    def aendre_bemaerkning(self, bilagsid: str, bemaerkning: str) -> None:
        """Ændrer bemærkningen på et bilag og verificerer at den blev gemt."""
        bemaerkning = bemaerkning[:59]
        frame = self._aabn_til_redigering(bilagsid, behandles=True, bogfoeres=True)
        frame.locator(bs.BEMAERKNING).fill(bemaerkning)
        institution = frame.locator(bs.INSTITUTION)
        if institution.count() > 0:
            institution.fill("")
        self._gem(bs.REDIGER_KNAP)

        gemt = (
            self._session.frame_med(bs.BEMAERKNING_VIS, bf.EBILAG, timeout=10_000)
            .locator(bs.BEMAERKNING_VIS)
            .first.inner_text()
        )
        if gemt.strip() != bemaerkning.strip():
            raise OESFejl(
                f"Angivet bemærkning '{bemaerkning}' og gemt bemærkning '{gemt}' "
                "matchede ikke"
            )

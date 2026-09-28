from typing import ClassVar


class LoginSelectors:
    # municipality email
    KOMMUNE_EMAIL = "#i0116"

    # next button after email
    NAESTE_BTN = "#idSIButton9"

    PASSWORD_FIELD = "#i0118"

    # login button after password
    LOGIN_BTN = "#idSIButton9"


class OESSelectors:
    # ------------------------------ Bruger Søgning // User Search --------------------------------

    # user id
    BRUGER_ID = "#idBRUGERID"

    # user details headline for assertion
    BRUGER_DETALJER_OVERSKRIFT = "body > form > table:nth-child(1) > tbody > tr:nth-child(1) > td > table > tbody > tr > td"

    # user id in user details for assertion
    BRUGER_DETALJER_ID = "#Fane_Brg > table > tbody > tr > td:nth-child(1) > table > tbody > tr:nth-child(2) > td.infocell"

    # ----------------------------------- Sletning // Deletion -------------------------------------

    # access group table
    ADGANGSGRUPPE_TABLE = "#Fane_Brg > table > tbody > tr > td:nth-child(3) > table > tbody > tr:nth-child(3) > td:nth-child(2) > table"

    # access group table - delete
    ADGANGSGRUPPE_TABLE_SLET = "#Fane_Brg > table > tbody > tr > td:nth-child(3) > table > tbody > tr:nth-child(3) > td:nth-child(2) > table > tbody > tr:nth-child(2) > td:nth-child(1) > a > img"

    # bogførings kasser // accounting fields
    KASSE_ET = "#idKasse1"
    KASSE_TO = "#idKasse2"
    KASSE_TRE = "#idKasse3"
    KASSE_FIRE = "#idKasse4"
    KASSE_FEM = "#idKasse5"
    KASSE_SEKS = "#idKasse6"

    # fields to clear in user tab
    CPR_NUMMER_VIS = "#idCPRNRVIS"
    AD_USER_ID = "#idaduserid"
    AFDELING_NUMMER = "#idAfdnr"
    INSTITUTION_NUMMER = "#idInstnr"
    SD_USER_ID = "#idsdUserId"

    # user blocked input
    BRUGER_SPAERRET = "#idSpaerr"

    # user blocked input after edit
    BRUGER_SPAERRET_EFTER_REDIGERING = "#Fane_Brg > table > tbody > tr > td:nth-child(1) > table > tbody > tr:nth-child(25) > td.infocell"

    # payment approval
    BETALING_GODKENDT = "#idBetgodk"

    # department table with department numbers
    AFDELINGSNUMMER_TABLE = "#Fane_Afd > table > tbody > tr > td > table"

    # department - delete line when there is only one row
    AFDELINGSNUMMER_TABLE_SLET = "#Fane_Afd > table > tbody > tr > td > table > tbody > tr.line1_topstreg > td:nth-child(1) > table > tbody > tr > td:nth-child(1) > a > img"

    # department - delete line when there are multiple rows (the delete button may get inlined and therefore has a different selector)
    AFDELINGSNUMMER_TABLE_SLET_TO = "#Fane_Afd > table > tbody > tr > td > table > tbody > tr.line1_topstreg > td:nth-child(1) > table > tbody > tr > td:nth-child(2) > a > img"

    # department from
    AFDELINGSNUMMER_TABLE_FRA = "#idAfdnrFra0"  # idAfdnrFra0

    # department to
    AFDELINGSNUMMER_TABLE_TIL = "#idAfdnrTil0"

    # institution table
    INSTITUTION_TABLE = "#Fane_Inst > table > tbody > tr > td > table"

    # institution - delete line
    INSTITUTION_TABLE_SLET = "#Fane_Inst > table > tbody > tr > td > table > tbody > tr.line1_topstreg > td:nth-child(1) > table > tbody > tr > td:nth-child(1) > a > img"

    # institution - delete line when there are multiple rows (the delete button may get inlined and therefore has a different selector)
    INSTITUTION_TABLE_SLET_TO = "#Fane_Inst > table > tbody > tr > td > table > tbody > tr.line1_topstreg > td:nth-child(1) > table > tbody > tr > td:nth-child(2) > a > img"

    # institution from
    INSTITUTION_TABLE_FRA = "#idInstnrFra_LKInstListe_0"

    # institution to
    INSTITUTION_TABLE_TIL = "#idInstnrTil_LKInstListe_0"

    # --------------------------------- Navigering // Navigation -----------------------------------

    # oes logo --> main page
    MAIN_PAGE = "https://odense.osi-local.dk/mod-core/#"

    # departement
    AFDELING_FANE = "#Fane_Afd_Inaktiv > a"

    # institution
    INSTITUTION_FANE = "#Fane_Inst_Inaktiv > a"


class OESCommands:
    # ---------------------------------- Handlinger // Commands ------------------------------------

    # the system handles changes by commands instead of ui buttons

    # edit user
    REDIGER_BRUGER = "Alt+3"

    # show user
    VIS_BRUGER = "Enter"
    # can also be "alt+v" instead of "enter"

    # clear / start over
    RYD_START_FORFRA = "Alt+R"

    # save user
    GEM_BRUGER = "Alt+2"


class BilagFrames:
    # ØS indlæser gamle JSP-sider i iframes under /mod-core-service/tab/<uuid>/os2000/...
    # uuid og ?T= ændrer sig ved hver indlæsning, så frames findes via sti-endelse (regex)
    # // ØS loads legacy JSPs in iframes; match frames by path suffix
    BILAGSOVERSIGT = r"/os2000/handel/oversigt\.jsp"
    BILAGSOVERSIGT_BTM = r"/os2000/handel/oversigt_btm\.jsp"
    EBILAG = r"/os2000/bilag/EBilag/EBilag\.jsp"
    EBILAG_BTM = r"/os2000/bilag/EBilag/EBilag_btm\.jsp"
    ORIGINAL_XML = r"/os2000/bilag/EBilag/OrigFaktOIOVis\.jsp"
    LOADING = r"/os2000/html/tom\.html"
    # alle knap-frames // any bottom button frame
    BTM = r"_btm\.jsp"


class BilagSelectors:
    # ------------------------------ Navigering // Navigation --------------------------------

    # sso knap på login siden i ØS // "Log på via SSO" button
    SSO_KNAP = "button.btn-sso"

    # overskrifter // page headers
    OPSAETNING_OVERSKRIFT = 'td.header:text-is("Opsætning")'
    BILAGSOVERSIGT_OVERSKRIFT = 'td.header:text-is("Bilagsoversigt")'
    FAKTURA_DETALJER_OVERSKRIFT = 'td.header:text-is("Faktura - detaljer")'

    # loading animation i tom.html frame // loading gif in tom.html frame
    LOADING_ANIMATION = "xpath=/html/body/table/tbody/tr/td/table/tbody/tr[2]/td[2]/img"

    # fejlliste // error list
    FEJLLISTE = "select#idFejlTekst"

    # ------------------------------ Bilagsoversigt // Search form ---------------------------

    REGNSKABSAAR_FRA = "select#idAarFra"
    REGNSKABSAAR_TIL = "select#idAarTil"
    AFDELINGSNR_FRA = "#idAfdnrFra"
    AFDELINGSNR_TIL = "#idAfdnrTil"
    # ligger på fanen "Andre kriterier" // on the hidden "Andre kriterier" tab
    CPRNR_FRA = "#idCprnrFra"
    CPRNR_TIL = "#idCprnrTil"
    DATO_TYPE = "select#idDatoType"
    DATO_FRA = "#idDatoFra"
    DATO_TIL = "#idDatoTil"
    BELOEB_TIL = "#idBelobMMTil"

    # søgningstype // search type (options: Fakturanr, Bestillingsnr, Ext. Bestillingsnr,
    # Bident, EANnr, UUID, Ext. sys - kun Bident er porteret // only Bident is ported)
    SOEGNINGSTYPE = "select#idBestilType"
    BIDENT = "#idBident"
    # øvrige søgefelter // other search fields: #idFaktnrFra, #idBestilFra,
    # #idEXTBESTILNRFra, #idEannrFra, #idUUID, #idExtsys

    # status checkboxe - navnene matcher ikke id'erne, mapping er fra Blue Prism
    # // status checkboxes - names do not match ids, mapping taken from Blue Prism
    STATUS_CHECKBOXE: ClassVar[dict[str, str]] = {
        "behandles": "#idFak_Varemodtaget",
        "foranvises": "#idFak_Foranvises",
        "konteret": "#idFak_Konterede",
        "bogfoeres": "#idFak_Bogfores",
        "efteranvises": "#idFak_Efteranvises",
        "bogfoert": "#idFak_Behandlede",
        "sendte": "#idFak_SendFejl",
        "kladde": "#idBes_Kladde",
        "inaktiveret": "#idFak_Annulerede",
    }

    # ------------------------------ Knapper i bunden // Bottom buttons ----------------------

    VIS_KNAP = 'input[alt^="Vis søgning"]'
    GEM_KNAP = 'input[alt^="Gem - Alt+2"]'
    REDIGER_KNAP = 'input[alt^="Rediger - Alt+3"]'
    # alt-teksten har dobbelt mellemrum før "-" // alt text has a double space before "-"
    VAREMODTAG_KNAP = 'input[alt^="Tryk her for at varemodtage fakturaen"]'
    TILBAGE_KNAP = 'input[name="Tilbage"]'
    NAESTE_SIDE = 'input[alt^="Næste side"]'
    FOERSTE_SIDE = 'input[alt^="Første side"]'
    SIDETALSVAELGER = "select#idSideantal"
    RESULTAT_TABEL = "td#maintable > table"

    # ------------------------------ Bilag // Invoice details --------------------------------

    BILAGSIDENTIFIKATION = "td.infocell"
    ORIGINAL_FANE = 'a.tab:text-is("Original")'
    XML_LINK = 'a:has-text("Klik her for at åbne xml")'

    BEMAERKNING = "#idBemaerkning"
    # gemt bemærkning i visningstilstand // saved remark in view mode (skal verificeres live)
    BEMAERKNING_VIS = "td.infocellwrap"

    # konteringslinjer - {n} er rækkens position fra 0 // kontering lines, {n} = row index
    BIDENT_LINJE = "#idBident_LKF_{n}"
    CPR_LINJE = "#idCprnr_LKF_{n}"
    KONTONR_LINJE = "#idKontoNr_LKF_{n}"
    POSTERINGSTEKST_LINJE = "#idPostext_LKF_{n}"
    BELOEB_LINJE = "#idBelobMM_LKF_{n}"
    DEBET_KREDIT_LINJE = "select#idDebkrd_LKF_{n}"
    SLET_LINJE = 'a[href*="raekkeSlet_LKF_,{n}\'"]'
    SLET_LINJER = 'a[href*="raekkeSlet_LKF_,"]'
    # tilføj linje efter række {n} - verificeret på ØS test (href
    # "javascript:setFunktionSubmit('EBilag','raekkeTilfoej_LKF_,0')")
    # // add line after row {n} - verified on ØS test
    TILFOEJ_LINJE = 'a[href*="raekkeTilfoej_LKF_,{n}\'"]'

    B_SKAT_LINJE = "select#idBskat_LKF_{n}"
    INSTITUTION = "#idInstitution_LKF_0"

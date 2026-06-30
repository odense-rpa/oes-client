class LoginSelectors:
    KOMMUNE_EMAIL = "#i0116"
    NAESTE_BTN = "#idSIButton9"
    PASSWORD_FIELD = "#i0118"
    LOGIN_BTN = "#idSIButton9"

class OESSelectors:
    # ----------------------------------- iframe & nested content --------------------------------

    # nogle af dem er måske redundante
    # dette vender jeg tilbage til

    # iframe
    IFRAME = "#iFrameId"

    # # frameset / content
    IFRAMESET = "#cursor > frameset"
    
    # content / specifik frame
    IFRAME_BRUGER = "#cursor > frameset > frameset > frame"

    # ------------------------------ Bruger Søgning // User Search --------------------------------

    # user id
    BRUGER_ID = "#idBRUGERID"

    # user details headline for assertion
    BRUGER_DETALJER_OVERSKRIFT = "body > form > table:nth-child(1) > tbody > tr:nth-child(1) > td > table > tbody > tr > td"

    # user id in user details for validation
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

    # user blocked
    BRUGER_SPAERRET = "#idSpaerr"

    # payment approval  
    BETALING_GODKENDT = "#idBetgodk"

    # department table with department numbers
    AFDELINGSNUMMER_TABLE = "#Fane_Afd > table > tbody > tr > td > table"

    # department - delete line
    AFDELINGSNUMMER_TABLE_SLET = "#Fane_Afd > table > tbody > tr > td > table > tbody > tr > td:nth-child(1) > table > tbody > tr > td:nth-child(1) > a > img"

    # department from
    AFDELINGSNUMMER_TABLE_FRA = "#idAfdnrFra0"

    # department to
    AFDELINGSNUMMER_TABLE_TIL = "#idAfdnrTil0"

    # institution table
    INSTITUTION_TABLE = "#Fane_Inst > table > tbody > tr > td > table"

    # institution - delete line
    INSTITUTION_TABLE_SLET = "#Fane_Inst > table > tbody > tr > td > table > tbody > tr > td:nth-child(1) > table > tbody > tr > td:nth-child(1) > a > img"

    # institution from
    INSTITUTION_TABLE_FRA = "#idInstnrFra_LKInstListe_0"

    # institution to
    INSTITUTION_TABLE_TIL = "#idInstnrTil_LKInstListe_0"
    
    # --------------------------------- Navigering // Navigation -----------------------------------

    # oes logo --> main page
    OES_LOGO = "body > app-root > div > mat-toolbar > div:nth-child(3) > div > div:nth-child(5) > img"

    # departement 
    AFDELING_FANE = "#Fane_Afd_Inaktiv > a"

    # institution
    INSTITUTION_FANE = "#Fane_Inst_Inaktiv > a"


class OESCommands:

    # ---------------------------------- Handlinger // Commands ------------------------------------

    # the system handles changes and deletion by commands instead of ui buttons

    # edit user
    REDIGER_BRUGER = "'Alt+3'"
    
    # show user
    VIS_BRUGER = "Enter"
    # can also be "alt+v" instead of "enter"

    # clear / start over
    RYD_START_FORFRA = "Alt" + "r"

    # save user
    GEM_BRUGER = "Alt+2"
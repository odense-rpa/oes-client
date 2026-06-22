class LoginSelectors:
    KOMMUNE_EMAIL = "#i0116"
    NAESTE_BTN = "#idSIButton9"
    PASSWORD_FIELD = "#i0118"
    LOGIN_BTN = "#idSIButton9"

class OESSelectors:
    # ----------------------------------- iframe & nested content --------------------------------

    # nogle af dem er måske redundante
    # eks kan måske blot bruge iframe_bruger uden iframeset
    # dette vender jeg tilbage til

    # iframe
    IFRAME = "#iFrameId"

    # # frameset / content
    IFRAMESET = "#cursor > frameset"
    
    # content / specifik frame
    IFRAME_BRUGER = "#cursor > frameset > frameset > frame"

    # form vi gerne vil tilgå
    #FORM = "body > form"



    
    OES_LOGO = "body > app-root > div > mat-toolbar > div:nth-child(3) > div > div:nth-child(5) > img"
    
    BRUGER_ID = "#idBRUGERID"

    BRUGER_DETALJER_OVERSKRIFT = "body > form > table:nth-child(1) > tbody > tr:nth-child(1) > td > table > tbody > tr > td"
    

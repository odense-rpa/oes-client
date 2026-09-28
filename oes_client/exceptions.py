"""Fejltyper for oes-client // Exception types for oes-client."""


class OESFejl(Exception):
    """Forretningsfejl fra ØS, fx valideringsfejl ved gem // Business error from ØS."""


class BilagIkkeFundet(OESFejl):
    """Bilaget kunne ikke findes med de givne søgekriterier."""

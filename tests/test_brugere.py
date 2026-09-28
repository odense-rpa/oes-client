"""Tests af brugeradministration mod ØS // User admin tests against ØS.

slet_bruger spærrer brugeren og kører kun med OES_ALLOW_WRITE=1.
"""

import pytest

skriv = pytest.mark.usefixtures("tillad_skriv")


def test_fremsoeg_bruger(oes, test_bruger_id):
    oes.brugere.fremsoeg_bruger(test_bruger_id)


@skriv
def test_slet_bruger(oes, test_bruger_id):
    oes.brugere.fremsoeg_bruger(test_bruger_id)
    oes.brugere.slet_bruger()

import pytest


def test_fremsoeg_bruger(oes_client, test_bruger_id):
    try:
        oes_client.fremsoeg_bruger(test_bruger_id)
    except Exception as e:
        pytest.fail(f"fremsoeg_bruger raised unexpected exception: {e}")


def test_slet_bruger_uden_at_gemme(oes_client, test_bruger_id):
    # udkommenter gem_bruger i client filen for at teste uden gem
    oes_client.fremsoeg_bruger(test_bruger_id)
    oes_client.slet_bruger()


def test_slet_bruger_med_gem(oes_client, test_bruger_id):
    oes_client.fremsoeg_bruger(test_bruger_id)
    oes_client.slet_bruger()

"""--dev-pro removido. O teste usa um argv controlado (não o sys.argv do pytest)."""
import sys

import main


def test_no_dev_pro_in_parse_args(monkeypatch):
    # controla argv para o argparse não ler os args reais do pytest
    monkeypatch.setattr(sys, "argv", ["airmouse", "--no-gui"])
    parser = main.parse_args()
    opts = set()
    for action in parser._actions:
        opts.update(action.option_strings)
    assert "--dev-pro" not in opts

"""Report output contract for the generated CLI."""

import json
import pytest
from jedocsops import cli


def test_report_formats(capsys):
    assert cli.main(["describe", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ok"
    assert cli.main(["describe", "--markdown"]) == 0
    assert capsys.readouterr().out.startswith("# ")
    with pytest.raises(SystemExit) as error:
        cli.main(["describe", "--json", "--markdown"])
    assert error.value.code == 2

"""Structural checks for the generated skeleton; not domain verification."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _flow():
    return json.loads((ROOT / "references/workflow/node-flow.json").read_text(encoding="utf-8"))


def test_manifest_name_matches_directory():
    manifest = json.loads((ROOT / "skill.manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == ROOT.name


def test_every_node_has_a_readme_and_is_in_the_flow():
    flow = _flow()
    for node_id in flow["nodes"]:
        assert (ROOT / "nodes" / node_id / "README.md").is_file(), node_id


def test_lanes_only_reference_known_nodes():
    flow = _flow()
    known = set(flow["nodes"])
    for lane in flow["lanes"].values():
        assert set(lane["nodes"]) <= known, lane


def test_node_flow_is_valid_json_contract():
    flow = _flow()
    assert flow["schema_version"] == 1
    assert flow["lanes"] and flow["nodes"]

"""The install command the README promises has to actually work.

The README's first code block is `claude plugin marketplace add ...` followed by
`claude plugin install ...`. That is a claim, and it shipped once without a
`.claude-plugin/marketplace.json` behind it -- so the command in the README
could not have worked for anyone who tried it.

These tests pin the three things that have to agree, because they are written in
three different files and drift silently:

    the marketplace entry  ==  the plugin manifest  ==  the README's install line
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGIN = REPO_ROOT / ".claude-plugin" / "plugin.json"
README = REPO_ROOT / "README.md"


def _marketplace():
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))


def test_the_marketplace_manifest_exists_and_parses():
    assert MARKETPLACE.exists(), (
        "without .claude-plugin/marketplace.json, "
        "`claude plugin marketplace add` fails and the README lies"
    )
    _marketplace()


def test_the_marketplace_declares_an_owner_and_a_plugin():
    d = _marketplace()
    assert d.get("name")
    assert d.get("owner", {}).get("name")
    assert d.get("plugins"), "a marketplace with no plugins installs nothing"


def test_the_plugin_entry_matches_the_plugin_manifest():
    entrada = _marketplace()["plugins"][0]
    manifiesto = json.loads(PLUGIN.read_text(encoding="utf-8"))
    assert entrada["name"] == manifiesto["name"], (
        f"marketplace offers {entrada['name']!r} but the plugin is "
        f"{manifiesto['name']!r}; `claude plugin install` would fail"
    )
    assert entrada.get("source"), "the entry needs a source or it points nowhere"


def test_the_readme_installs_the_name_the_marketplace_offers():
    text = README.read_text(encoding="utf-8")
    ofrecido = _marketplace()["plugins"][0]["name"]
    instalados = re.findall(r"claude plugin install ([\w-]+)", text)
    assert instalados, "the README no longer tells anyone how to install it"
    assert set(instalados) == {ofrecido}, (
        f"README installs {sorted(set(instalados))}, marketplace offers {ofrecido!r}"
    )


def test_the_readme_adds_the_repository_that_actually_hosts_it():
    text = README.read_text(encoding="utf-8")
    fuentes = re.findall(r"claude plugin marketplace add ([\w./-]+)", text)
    assert fuentes, "the README no longer says which marketplace to add"
    for fuente in fuentes:
        assert fuente == "everywan-dev/claude-code-engineering", (
            f"README points at {fuente!r}, which is not this repository"
        )

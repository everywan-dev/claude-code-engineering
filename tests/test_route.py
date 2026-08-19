"""End-to-end tests for `validated-memory route`.

Same seam as the rest of the suite: the CLI as a subprocess, asserting on exit
codes and output. Nothing here imports the package's internals.

The tests worth having are the ones that could fail in a way that matters:

- a change that *sounds* harmless but touches a dangerous path must not come
  back as cheap;
- an unrecognised change must default upward, not downward;
- and level 3 must never be paired with the small model, which is the one rule
  the whole model assignment rests on.
"""

import json

import pytest

LEVEL_3_PHRASES = [
    "change the password reset flow",
    "add a role to the admin panel",
    "adjust how refunds are calculated",
    "export customer data to a csv",
    "write a migration that drops the old column",
    "open a firewall rule for the new service",
    "renew the TLS certificate",
    "roll this out to every tenant",
]


def test_route_is_listed_as_a_subcommand(adopter_dir, run_cli):
    result = run_cli("--help", cwd=adopter_dir)
    assert result.returncode == 0
    assert "route" in result.stdout


def test_cosmetic_work_is_level_1_on_the_small_model(adopter_dir, run_cli):
    result = run_cli("route", "fix a typo in the README", cwd=adopter_dir)
    assert result.returncode == 0
    assert "Level 1" in result.stdout
    assert "haiku" in result.stdout


def test_production_work_is_level_2_with_two_independent_validations(adopter_dir, run_cli):
    result = run_cli("route", "bump the dependency and redeploy", cwd=adopter_dir)
    assert result.returncode == 0
    assert "Level 2" in result.stdout
    assert "2 validations" in result.stdout
    assert "sonnet" in result.stdout
    # The definition of independence has to travel with the answer, or the
    # number is just a number.
    assert "does not receive" in result.stdout


@pytest.mark.parametrize("phrase", LEVEL_3_PHRASES)
def test_dangerous_work_is_level_3(phrase, adopter_dir, run_cli):
    result = run_cli("route", phrase, cwd=adopter_dir)
    assert result.returncode == 0
    assert "Level 3" in result.stdout, f"{phrase!r} should be level 3"
    assert "devils-advocate" in result.stdout


@pytest.mark.parametrize("phrase", LEVEL_3_PHRASES)
def test_level_3_never_runs_on_the_small_model(phrase, adopter_dir, run_cli):
    """The one hard rule. Saving tokens is fine where being wrong is cheap."""
    result = run_cli("route", phrase, "--json", cwd=adopter_dir)
    decision = json.loads(result.stdout)
    assert decision["level"] == 3
    assert decision["model"] != "haiku"


def test_a_dangerous_path_outranks_a_harmless_description(adopter_dir, run_cli):
    """"Small tweak" is a description of intent, not of risk."""
    result = run_cli(
        "route", "just a small tweak", "--path", "db/migrations/004_drop_users.sql",
        cwd=adopter_dir,
    )
    assert result.returncode == 0
    assert "Level 3" in result.stdout


def test_unrecognised_work_defaults_upward_and_says_so(adopter_dir, run_cli):
    """Being wrong upward costs a review. Downward costs an incident."""
    result = run_cli("route", "frobnicate the widgets", cwd=adopter_dir)
    assert result.returncode == 0
    assert "Level 2" in result.stdout
    assert "No signal matched" in result.stdout
    # It must not present the guess as a reading of the change.
    assert "not a measurement" in result.stdout


def test_json_output_carries_the_whole_decision(adopter_dir, run_cli):
    result = run_cli("route", "redeploy the api", "--json", cwd=adopter_dir)
    assert result.returncode == 0
    decision = json.loads(result.stdout)
    for key in ("level", "validations", "model", "effort", "agents", "rule",
                "matched", "defaulted"):
        assert key in decision, f"missing {key!r}"
    assert isinstance(decision["agents"], list) and decision["agents"]


def test_it_advises_and_never_gates(adopter_dir, run_cli):
    """`route` answers a question; it is not a check that can fail a build."""
    for phrase in ("", "anything at all", "drop the production database"):
        result = run_cli("route", phrase, cwd=adopter_dir)
        assert result.returncode == 0

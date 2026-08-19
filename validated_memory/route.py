"""Route a piece of work to a validation level, a set of agents, and a model.

Invoked as `validated-memory route "<what you are about to do>"`.

======================================================================
WHY THIS IS A COMMAND AND NOT A JUDGEMENT CALL
======================================================================
Deciding how much validation a change needs, per change, in the moment, is how
teams end up validating nothing. The decision is always made under pressure by
the person who most wants the answer to be "not much".

So the decision is made in advance, from the kind of work, by a table. This
module is that table. It is deliberately dumb: it matches signals in the text
and in the touched paths. It does not understand your change and does not
pretend to.

======================================================================
THE ONE DESIGN DECISION THAT MATTERS
======================================================================
When nothing matches, it does **not** fall back to the cheapest answer.

Being wrong upward costs a review nobody needed. Being wrong downward costs an
incident. Those are not symmetric, so the default is not symmetric either: an
unrecognised change is treated as production work (level 2), and the output says
plainly that no signal matched and what would raise it to 3.

The same asymmetry gives the hard rule of the model assignment:

    Nothing at level 3 runs on the small model.

Saving tokens is worth it exactly where being wrong is cheap.
"""

import json
import re

# --------------------------------------------------------------------
# Signals. Substrings, matched case-insensitively against the description
# and against any paths given. Kept as plain words on purpose: this file is
# meant to be read and argued with by the team that owns the risk.
# --------------------------------------------------------------------

LEVEL_3_SIGNALS = {
    "authentication": ["login", "log in", "signin", "sign in", "auth", "oauth", "sso",
                       "password", "credential", "token", "session", "jwt", "mfa", "2fa"],
    "permissions": ["permission", "role", "rbac", "acl", "privilege", "grant", "sudo",
                    "admin access", "authorization", "authorisation"],
    "money": ["payment", "invoice", "billing", "price", "refund", "charge", "balance",
              "checkout", "subscription", "tax", "ledger", "payout"],
    "customer data": ["customer data", "personal data", "pii", "gdpr", "patient",
                      "medical record", "export data", "user data"],
    "data destruction": ["migration", "migrate schema", "drop table", "truncate",
                         "delete from", "backfill", "purge", "wipe", "alter table"],
    "network": ["firewall", "nat", "routing", "bgp", "vlan", "dns record", "load balancer",
                "reverse proxy", "traefik", "nginx config", "ingress", "vpn", "port forward"],
    "certificates": ["certificate", "tls", "ssl", "letsencrypt", "acme", "renewal"],
    # Singular and plural both, because "roll this out to every tenant" is the
    # same blast radius as "all tenants" and a test caught exactly that gap.
    "fleet-wide": ["every site", "all sites", "every tenant", "all tenants",
                   "every customer", "all customers", "every node", "all nodes",
                   "fleet", "all environments", "every environment", "across the estate"],
}

LEVEL_2_SIGNALS = {
    "production code": ["production", "prod ", "deploy", "release", "rollout", "hotfix"],
    "service configuration": ["docker", "compose", "kubernetes", "k8s", "swarm", "systemd",
                              "service config", "environment variable", "env var"],
    "ci": ["pipeline", "ci/cd", "ci ", "github actions", "gitlab-ci", "workflow", "runner"],
    "dependencies": ["dependency", "dependencies", "upgrade", "bump version", "package.json",
                     "requirements.txt", "lockfile", "npm install", "pip install"],
}

LEVEL_1_SIGNALS = {
    "cosmetic": ["typo", "wording", "copy change", "readme", "comment", "docstring",
                 "changelog", "translation", "rename variable", "formatting", "lint fix"],
    "documentation": ["documentation", "docs ", "adr", "runbook text", "blog post"],
}

# Paths carry risk regardless of how the change is described.
PATH_SIGNALS_3 = [
    "migrations/", "schema.sql", "auth", "login", "payment", "billing",
    "firewall", "nginx.conf", "traefik", "secrets", ".env",
]
PATH_SIGNALS_2 = [
    "dockerfile", "docker-compose", ".gitlab-ci", ".github/workflows",
    "requirements.txt", "package.json", "pyproject.toml",
]

# --------------------------------------------------------------------
# The table. Levels come from docs/validation-levels.md; this is its
# executable form, and the doc is the prose form. They must agree.
# --------------------------------------------------------------------

PLAN = {
    1: {
        "validations": 1,
        "model": "haiku",
        "effort": "low",
        "agents": ["frontend-reviewer", "documenter"],
        "rule": "One review. Pick whichever of the two fits the change.",
    },
    2: {
        "validations": 2,
        "model": "sonnet",
        "effort": "medium",
        "agents": ["tests", "infra-reviewer"],
        "rule": "Two independent reviews. The implementer is not one of them.",
    },
    3: {
        "validations": 3,
        "model": "opus",
        "effort": "high",
        "agents": ["security-reviewer", "data-reviewer", "devils-advocate"],
        "rule": ("Three, and the devil's advocate has to actively try to break it. "
                 "Approving is not its job."),
    },
}

SMALL_MODEL = "haiku"


def _hits(text, signals):
    """Returns the matched categories and the words that matched them.

    Matching is on whole words, not substrings. Plain `in` reported "load
    balancer" as a money signal, because "balance" is inside "balancer". It did
    not change that particular verdict -- the phrase was already level 3 for
    other reasons -- but a checker that reports a match it did not really find
    is a checker you cannot read, and the whole value of this command is that
    you can see why it decided what it decided.
    """
    found = {}
    for category, words in signals.items():
        matched = [
            p for p in words
            # Optional plural: "refund" has to find "refunds". This still does
            # not match "balancer" from "balance", which needs an "r", not an "s".
            if re.search(rf"(?<![\w-]){re.escape(p)}(?:e?s)?(?![\w-])", text)
        ]
        if matched:
            found[category] = matched
    return found


def classify(description, paths=None):
    """Classify work into a level. Returns a dict; never raises on odd input.

    `paths` are the files the change touches, if known. A path can raise the
    level on its own: a change described as "small tweak" that edits
    `migrations/` is not a small tweak.
    """
    text = " ".join([description or ""] + list(paths or [])).lower()
    # normalise separators so "auth_service" and "auth-service" both match "auth"
    text = re.sub(r"[_/\\]", " ", text) + " "
    paths = " ".join(paths or []).lower()

    three = _hits(text, LEVEL_3_SIGNALS)
    ruta3 = [p for p in PATH_SIGNALS_3 if p in paths]
    if ruta3:
        three.setdefault("touched path", []).extend(ruta3)
    if three:
        return _result(3, three, False)

    two = _hits(text, LEVEL_2_SIGNALS)
    ruta2 = [p for p in PATH_SIGNALS_2 if p in paths]
    if ruta2:
        two.setdefault("touched path", []).extend(ruta2)
    if two:
        return _result(2, two, False)

    one = _hits(text, LEVEL_1_SIGNALS)
    if one:
        return _result(1, one, False)

    # Nothing matched. Do NOT drop to level 1: see the module docstring.
    return _result(2, {}, True)


def _result(level, signals, defaulted):
    plan = PLAN[level]
    output = {
        "level": level,
        "validations": plan["validations"],
        "model": plan["model"],
        "effort": plan["effort"],
        "agents": list(plan["agents"]),
        "rule": plan["rule"],
        "matched": {k: sorted(set(v)) for k, v in signals.items()},
        "defaulted": defaulted,
    }
    # The hard rule, asserted rather than assumed.
    if output["level"] == 3 and output["model"] == SMALL_MODEL:
        raise AssertionError("level 3 must never run on the small model")
    return output


def _render(r):
    lines = []
    headline = f"Level {r['level']} — {r['validations']} validation" + ("s" if r["validations"] > 1 else "")
    lines.append(headline)
    lines.append("")
    if r["defaulted"]:
        lines.append("No signal matched, so this is treated as production work.")
        lines.append("That is the safe direction, not a measurement of your change.")
        lines.append("If it touches authentication, money, customer data, migrations,")
        lines.append("network rules or certificates, it is level 3 — say so and re-run.")
    else:
        for category, words in sorted(r["matched"].items()):
            lines.append(f"  matched {category}: {', '.join(words)}")
    lines.append("")
    lines.append(f"  model   : {r['model']}")
    lines.append(f"  effort  : {r['effort']}")
    lines.append(f"  agents  : {', '.join(r['agents'])}")
    lines.append("")
    lines.append(f"  {r['rule']}")
    if r["level"] >= 2:
        lines.append("")
        lines.append("  Independent means the validator does not receive the")
        lines.append("  implementer's reasoning. Reviewing your own work again is not")
        lines.append("  a second validation: the blind spots travel with you.")
    return "\n".join(lines)


def run(description, paths=None, as_json=False, stream=None):
    """Entry point used by the CLI. Always exits 0: this advises, it does not gate."""
    result = classify(description, paths)
    output = json.dumps(result, indent=2, sort_keys=True) if as_json else _render(result)
    print(output, file=stream)
    return 0

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


def _hits(texto, senales):
    """Returns the matched categories and the words that matched them."""
    encontrados = {}
    for categoria, palabras in senales.items():
        coincide = [p for p in palabras if p in texto]
        if coincide:
            encontrados[categoria] = coincide
    return encontrados


def classify(description, paths=None):
    """Classify work into a level. Returns a dict; never raises on odd input.

    `paths` are the files the change touches, if known. A path can raise the
    level on its own: a change described as "small tweak" that edits
    `migrations/` is not a small tweak.
    """
    texto = " ".join([description or ""] + list(paths or [])).lower()
    # normalise separators so "auth_service" and "auth-service" both match "auth"
    texto = re.sub(r"[_/\\]", " ", texto) + " "
    rutas = " ".join(paths or []).lower()

    tres = _hits(texto, LEVEL_3_SIGNALS)
    ruta3 = [p for p in PATH_SIGNALS_3 if p in rutas]
    if ruta3:
        tres.setdefault("touched path", []).extend(ruta3)
    if tres:
        return _resultado(3, tres, False)

    dos = _hits(texto, LEVEL_2_SIGNALS)
    ruta2 = [p for p in PATH_SIGNALS_2 if p in rutas]
    if ruta2:
        dos.setdefault("touched path", []).extend(ruta2)
    if dos:
        return _resultado(2, dos, False)

    uno = _hits(texto, LEVEL_1_SIGNALS)
    if uno:
        return _resultado(1, uno, False)

    # Nothing matched. Do NOT drop to level 1: see the module docstring.
    return _resultado(2, {}, True)


def _resultado(nivel, senales, por_defecto):
    plan = PLAN[nivel]
    salida = {
        "level": nivel,
        "validations": plan["validations"],
        "model": plan["model"],
        "effort": plan["effort"],
        "agents": list(plan["agents"]),
        "rule": plan["rule"],
        "matched": {k: sorted(set(v)) for k, v in senales.items()},
        "defaulted": por_defecto,
    }
    # The hard rule, asserted rather than assumed.
    if salida["level"] == 3 and salida["model"] == SMALL_MODEL:
        raise AssertionError("level 3 must never run on the small model")
    return salida


def _render(r):
    lineas = []
    cabecera = f"Level {r['level']} — {r['validations']} validation" + ("s" if r["validations"] > 1 else "")
    lineas.append(cabecera)
    lineas.append("")
    if r["defaulted"]:
        lineas.append("No signal matched, so this is treated as production work.")
        lineas.append("That is the safe direction, not a measurement of your change.")
        lineas.append("If it touches authentication, money, customer data, migrations,")
        lineas.append("network rules or certificates, it is level 3 — say so and re-run.")
    else:
        for categoria, palabras in sorted(r["matched"].items()):
            lineas.append(f"  matched {categoria}: {', '.join(palabras)}")
    lineas.append("")
    lineas.append(f"  model   : {r['model']}")
    lineas.append(f"  effort  : {r['effort']}")
    lineas.append(f"  agents  : {', '.join(r['agents'])}")
    lineas.append("")
    lineas.append(f"  {r['rule']}")
    if r["level"] >= 2:
        lineas.append("")
        lineas.append("  Independent means the validator does not receive the")
        lineas.append("  implementer's reasoning. Reviewing your own work again is not")
        lineas.append("  a second validation: the blind spots travel with you.")
    return "\n".join(lineas)


def run(description, paths=None, as_json=False, stream=None):
    """Entry point used by the CLI. Always exits 0: this advises, it does not gate."""
    resultado = classify(description, paths)
    salida = json.dumps(resultado, indent=2, sort_keys=True) if as_json else _render(resultado)
    print(salida, file=stream)
    return 0

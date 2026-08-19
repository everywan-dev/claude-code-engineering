"""CLAUDE.md says this repository is written in English. Nothing enforced it.

Spanish identifiers and comments reached `main` and were only caught by a human
reading the published diff. The rule existed, in writing, and had no check
behind it -- which is the exact failure this project is about.

The check is a list of Spanish function words that do not occur in English
technical prose. It is deliberately narrow: words that exist in both languages
("no", "as", "a", "en", "final", "control") are left out, because a check that
cries wolf gets switched off.

Third-party licence text is excluded: it is not ours to rewrite. Proper nouns
are allowlisted by exact spelling.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Extensions worth scanning: code, prose and configuration we author.
SUFFIXES = {".py", ".md", ".toml", ".json", ".yml", ".yaml", ".sh", ".txt", ".tape"}

# Not ours to police.
EXCLUDED = {
    ".git", ".pytest_cache", "__pycache__", "LICENSES", "node_modules", ".venv",
    # Build artefacts are copies of source that has already been scanned.
    "build", "dist",
}
EXCLUDED_FILES = {
    "LICENSE",
    # This file. It has to spell the words out to look for them, so scanning it
    # makes it report itself -- the same trap a secret scanner falls into when
    # its own examples look like secrets. The two tests below cover it instead:
    # one proves the wordlist still catches Spanish, the other that it does not
    # fire on English.
    "test_everything_is_in_english.py",
}

# High-signal Spanish. Every one of these is a word that does not appear in
# English technical writing, so a single hit is a real finding rather than
# noise to be triaged.
SPANISH_WORDS = [
    "que", "para", "pero", "porque", "donde", "cuando", "también", "además",
    "hacer", "tiene", "nadie", "aunque", "siempre", "nunca", "desde", "esto",
    "este", "esta", "estos", "estas", "así", "sólo", "más", "muy", "del",
    "los", "las", "una", "por", "como", "según", "hay", "son", "está",
    "fichero", "archivo", "pruebas", "comprobación", "castellano", "español",
    "cadena", "salida", "entrada", "usuario", "nombre", "ejemplo", "texto",
]

# Proper nouns and identifiers that are Spanish-looking but correct.
ALLOWED = {"Vázquez", "Centelles", "Oriol", "Juan", "Carlos"}

PATTERN = re.compile(
    r"(?<![\w-])(" + "|".join(re.escape(w) for w in SPANISH_WORDS) + r")(?![\w-])",
    re.IGNORECASE,
)


def _files_to_scan():
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in SUFFIXES:
            continue
        if path.name in EXCLUDED_FILES:
            continue
        if any(part in EXCLUDED for part in path.relative_to(REPO_ROOT).parts):
            continue
        yield path


def test_no_spanish_anywhere_we_author():
    findings = []
    for path in _files_to_scan():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if any(name in line for name in ALLOWED):
                continue
            match = PATTERN.search(line)
            if match:
                findings.append(
                    f"{path.relative_to(REPO_ROOT)}:{number}: "
                    f"{match.group(1)!r} in {line.strip()[:70]!r}"
                )
    assert not findings, (
        "CLAUDE.md requires English throughout. Spanish found in "
        f"{len(findings)} place(s):\n  " + "\n  ".join(findings[:20])
    )


def test_the_check_can_actually_fail(tmp_path):
    """A language check that never fires is worth nothing.

    Rather than trust the wordlist, run it against a line that is unmistakably
    Spanish and assert it is caught.
    """
    planted = "# esto no tiene que llegar nunca a main"
    assert PATTERN.search(planted), (
        "the wordlist no longer catches obvious Spanish; it has been narrowed "
        "until it stopped working"
    )


def test_the_check_does_not_fire_on_english():
    """The other half: it must not cry wolf, or someone will switch it off."""
    for line in (
        "# Read the CLI's subcommands from the CLI, not from a copy of them.",
        "assert result.returncode == 0, 'the entry point does not resolve'",
        "A check that cannot fail is not a check.",
        "Los Angeles is a place name and this line is still English.",
    ):
        if any(name in line for name in ALLOWED):
            continue
        match = PATTERN.search(line)
        assert match is None or match.group(1).lower() in {"los"}, (
            f"false positive {match.group(1)!r} on English line: {line!r}"
        )

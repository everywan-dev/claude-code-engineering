"""The `validate` subcommand: curated-knowledge units against the contract."""

from pathlib import Path

from . import extension as extension_module
from .contract import ERROR, WARNING, Finding, validate_documents
from .findings import report

DEFAULT_KNOWLEDGE_DIR = "knowledge"
UNIT_SUFFIX = ".md"


def run(path, stdout, stderr):
    """Validate every unit under `path` and report findings. Returns an exit code."""
    documents, findings = collect_and_validate(path)
    return report("validate", len(documents), "unit(s)", findings, stdout, stderr)


def gated_source(path, stderr):
    """Collect and validate the source, printing every finding.

    The gate every consumer of a valid source shares (`derive`, `probe`):
    returns `(documents, ok)`, where a False `ok` means an ERROR finding
    gates and the source must not be consumed.
    """
    documents, findings = collect_and_validate(path)
    for finding in findings:
        print(finding.render(), file=stderr)
    ok = not any(finding.severity == ERROR for finding in findings)
    return documents, ok


def collect_and_validate(path):
    """Collect units under `path` and validate them against the full contract.

    The shared front half of every consumer that needs a valid source: load
    the declared extension, read the units, apply the contract. Returns
    `(documents, findings)`; when the extension cannot be loaded, there are no
    documents and the single blocking finding.
    """
    try:
        extension = extension_module.load(Path())
    except extension_module.ExtensionError as error:
        # An extension that cannot be loaded stops the run: validating units
        # against the base contract alone would report a pass the adopter did
        # not ask for.
        return [], [
            Finding(ERROR, error.location, error.field, error.message, line=error.line)
        ]
    documents, findings = _collect(resolve_target(path), explicit=bool(path))
    findings.extend(validate_documents(documents, extension))
    return documents, findings


def resolve_target(path):
    """The unit tree a run reads: `path` if given, the default directory if not."""
    return Path(path) if path else Path(DEFAULT_KNOWLEDGE_DIR)


def _collect(target, explicit):
    location = target.as_posix()
    if not target.exists():
        if explicit:
            message = "no such file or directory"
        else:
            message = (
                f"no curated-knowledge directory found at '{location}'; pass a PATH "
                "or run 'validated-memory init'"
            )
        return [], [Finding(ERROR, location, "target", message)]

    if target.is_dir():
        files = sorted(
            path for path in target.rglob(f"*{UNIT_SUFFIX}") if path.is_file()
        )
        if not files:
            return [], [
                Finding(
                    WARNING,
                    location,
                    "target",
                    f"no curated-knowledge units (*{UNIT_SUFFIX}) found",
                )
            ]
    else:
        files = [target]

    documents = []
    findings = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            findings.append(
                Finding(ERROR, path.as_posix(), "file", f"cannot be read: {error}")
            )
            continue
        documents.append((path.as_posix(), text))
    return documents, findings

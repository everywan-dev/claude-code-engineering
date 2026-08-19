"""The shared finding type: one reportable observation, ERROR or WARNING.

Both `validate` (curated knowledge) and `lint` (agent memory) report the same
shape of finding, so it lives here rather than under either enforcement
module.
"""

ERROR = "ERROR"
WARNING = "WARNING"

EXIT_OK = 0
EXIT_ERROR = 1


class Finding:
    """One reportable observation about one document.

    `line` is set only when the finding has one: the parser knows where it
    stopped, while a document-level rule usually speaks about the document as
    a whole.
    """

    __slots__ = ("field", "line", "location", "message", "severity")

    def __init__(self, severity, location, field, message, line=None):
        self.severity = severity
        self.location = location
        self.field = field
        self.message = message
        self.line = line

    def render(self):
        where = self.location if self.line is None else f"{self.location}:{self.line}"
        return f"{self.severity}: {where}: {self.field}: {self.message}"


def report(command, checked, noun, findings, stdout, stderr):
    """Print the findings and the one-line summary; return the exit code.

    The summary names what was counted (`checked` of `noun`), so every
    enforcement command reports through the same shape and gates the same way:
    any ERROR exits 1, WARNINGs alone exit 0.
    """
    errors = [finding for finding in findings if finding.severity == ERROR]
    warnings = [finding for finding in findings if finding.severity == WARNING]
    for finding in findings:
        print(finding.render(), file=stderr)
    print(
        f"{command}: {checked} {noun} checked, "
        f"{len(errors)} error(s), {len(warnings)} warning(s)",
        file=stdout,
    )
    return EXIT_ERROR if errors else EXIT_OK

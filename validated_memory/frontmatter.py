"""Parser for the YAML subset the contract defines.

This is not a YAML parser. It understands exactly the shapes a curated
knowledge unit needs -- mappings, lists, nested blocks, empty inline
collections and quoted or plain scalars -- and raises on everything else.
There is no best effort, no implicit typing and no silent recovery: whatever
the parser does not understand is an error the caller reports.

Scalars are always strings. Numbers, booleans and nulls are not inferred; a
value that should be typed is interpreted downstream, by whoever owns its
meaning.
"""

import re

KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
ENTRY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*:(\s|$)")

FENCE = "---"


class FrontmatterError(Exception):
    """Raised when the frontmatter falls outside the supported subset."""

    def __init__(self, message, lineno):
        super().__init__(message)
        self.message = message
        self.lineno = lineno


class _Line:
    __slots__ = ("indent", "lineno", "text")

    def __init__(self, indent, text, lineno):
        self.indent = indent
        self.text = text
        self.lineno = lineno


def parse(text):
    """Parse the frontmatter of a document and return it as a mapping."""
    lines = text.split("\n")
    if not lines or lines[0].rstrip() != FENCE:
        raise FrontmatterError(
            "missing frontmatter: the file must start with a '---' line", 1
        )
    closing = None
    for index in range(1, len(lines)):
        if lines[index].rstrip() == FENCE:
            closing = index
            break
    if closing is None:
        raise FrontmatterError(
            "unterminated frontmatter: no closing '---' line", len(lines)
        )

    tokens = _tokenize(lines[1:closing], first_lineno=2)
    if not tokens:
        raise FrontmatterError("empty frontmatter", 1)
    if tokens[0].indent != 0:
        raise FrontmatterError("frontmatter must start at column 0", tokens[0].lineno)
    data = _parse_block(tokens)
    if not isinstance(data, dict):
        raise FrontmatterError("frontmatter must be a mapping", tokens[0].lineno)
    return data


def _tokenize(raw_lines, first_lineno):
    tokens = []
    for offset, raw in enumerate(raw_lines):
        lineno = first_lineno + offset
        if "\t" in raw:
            raise FrontmatterError("tabs are not allowed in frontmatter", lineno)
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        content = raw.rstrip()
        indent = len(content) - len(content.lstrip(" "))
        tokens.append(_Line(indent, content[indent:], lineno))
    return tokens


def _parse_block(lines):
    base = lines[0].indent
    for line in lines:
        if line.indent < base:
            raise FrontmatterError("inconsistent indentation", line.lineno)
    if lines[0].text.startswith("-"):
        return _parse_list(lines, base)
    return _parse_mapping(lines, base)


def _split_entries(lines, base):
    chunks = []
    for line in lines:
        if line.indent == base:
            chunks.append([line])
        else:
            chunks[-1].append(line)
    return chunks


def _parse_mapping(lines, base):
    result = {}
    for chunk in _split_entries(lines, base):
        head = chunk[0]
        if head.text.startswith("-"):
            raise FrontmatterError(
                "expected a 'key: value' entry, found a list item", head.lineno
            )
        key, separator, remainder = head.text.partition(":")
        if not separator:
            raise FrontmatterError("expected a 'key: value' entry", head.lineno)
        key = key.strip()
        if not KEY_PATTERN.match(key):
            raise FrontmatterError(f"invalid key '{key}'", head.lineno)
        if key in result:
            raise FrontmatterError(f"duplicate key '{key}'", head.lineno)
        value_text = _cut_comment(remainder, head.lineno)
        if value_text:
            # The scalar is parsed first so that unsupported syntax is reported
            # where it appears, not as a side effect of the lines below it.
            value = _parse_scalar(value_text, head.lineno)
            if len(chunk) > 1:
                raise FrontmatterError(
                    f"key '{key}' has both an inline value and an indented block",
                    head.lineno,
                )
            result[key] = value
        elif len(chunk) > 1:
            result[key] = _parse_block(chunk[1:])
        else:
            raise FrontmatterError(
                f"key '{key}' has no value; write '[]' or '{{}}' for an empty "
                "collection",
                head.lineno,
            )
    return result


def _parse_list(lines, base):
    items = []
    for chunk in _split_entries(lines, base):
        head = chunk[0]
        if not head.text.startswith("-"):
            raise FrontmatterError("expected a list item starting with '- '", head.lineno)
        remainder = head.text[1:]
        if remainder and not remainder.startswith(" "):
            raise FrontmatterError("expected a space after '-'", head.lineno)
        content = remainder.strip()
        if not content or content.startswith("#"):
            if len(chunk) == 1:
                raise FrontmatterError("empty list item", head.lineno)
            items.append(_parse_block(chunk[1:]))
            continue
        if len(chunk) == 1 and not ENTRY_PATTERN.match(content):
            items.append(_parse_scalar(_cut_comment(content, head.lineno), head.lineno))
            continue
        column = base + 1 + (len(remainder) - len(remainder.lstrip(" ")))
        items.append(_parse_block([_Line(column, content, head.lineno)] + chunk[1:]))
    return items


def _cut_comment(raw, lineno):
    """Drop a trailing comment, honouring a leading quoted scalar."""
    text = raw.strip()
    if not text or text.startswith("#"):
        return ""
    if text[0] in "\"'":
        quote = text[0]
        end = text.find(quote, 1)
        if end == -1:
            raise FrontmatterError("unterminated quoted string", lineno)
        trailing = text[end + 1 :].strip()
        if trailing and not trailing.startswith("#"):
            raise FrontmatterError("unexpected text after a quoted string", lineno)
        return text[: end + 1]
    marker = text.find(" #")
    if marker != -1:
        text = text[:marker].rstrip()
    return text


def _parse_scalar(text, lineno):
    if text == "[]":
        return []
    if text == "{}":
        return {}
    first = text[0]
    if first in "[{":
        raise FrontmatterError(
            "inline collections are only supported when empty ('[]' or '{}'); "
            "use an indented block",
            lineno,
        )
    if first in "&*!|>%@`?,":
        raise FrontmatterError(f"unsupported YAML syntax '{first}'", lineno)
    if first in "\"'":
        inner = text[1:-1]
        if "\\" in inner:
            raise FrontmatterError(
                "backslash escapes are not supported inside quoted strings", lineno
            )
        return inner
    return text

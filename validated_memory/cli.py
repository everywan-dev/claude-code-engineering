"""Command-line interface for validated-memory.

Exit code convention:
  0  clean run, or WARNING-level findings only (does not gate)
  1  ERROR-level findings or execution failure (gates)
  2  usage error (argparse)
"""

import argparse
import sys

from . import __version__, derive, init, lint, probe, route, validate

SUBCOMMANDS = {
    "init": "Scaffold the validated-memory layout in an adopter project",
    "lint": "Lint the agent-memory layer: index sync, frontmatter, wikilinks, supersession",
    "validate": "Validate curated-knowledge units against the base contract",
    "derive": "Re-derive indexes and summaries from curated-knowledge units",
    "probe": "Run freshness probes and record ternary verdicts",
    "route": "Decide how much validation a change needs, and which agents and model",
}


def build_parser():
    parser = argparse.ArgumentParser(
        prog="validated-memory",
        description="Enforcement CLI for the validated-memory plugin.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, metavar="<command>"
    )
    for name, help_text in SUBCOMMANDS.items():
        subparser = subparsers.add_parser(name, help=help_text, description=help_text)
        if name == "validate":
            subparser.add_argument(
                "path",
                nargs="?",
                metavar="PATH",
                help=(
                    "unit file or directory to validate "
                    f"(default: {validate.DEFAULT_KNOWLEDGE_DIR}/)"
                ),
            )
        if name == "derive":
            subparser.add_argument(
                "path",
                nargs="?",
                metavar="PATH",
                help=(
                    "unit file or directory to derive the index from "
                    f"(default: {validate.DEFAULT_KNOWLEDGE_DIR}/)"
                ),
            )
            subparser.add_argument(
                "--check",
                action="store_true",
                help=(
                    "recalculate without writing; fail if the on-disk index "
                    f"({derive.INDEX_FILENAME}) does not match"
                ),
            )
        if name == "lint":
            subparser.add_argument(
                "path",
                nargs="?",
                metavar="PATH",
                help=(
                    "agent-memory directory to lint "
                    f"(default: {lint.DEFAULT_MEMORY_DIR}/)"
                ),
            )
        if name == "probe":
            subparser.add_argument(
                "path",
                nargs="?",
                metavar="PATH",
                help=(
                    "unit file or directory to probe "
                    f"(default: {validate.DEFAULT_KNOWLEDGE_DIR}/)"
                ),
            )
        if name == "route":
            subparser.add_argument(
                "description",
                metavar="DESCRIPTION",
                help="what you are about to do, in your own words",
            )
            subparser.add_argument(
                "--path",
                action="append",
                default=[],
                metavar="PATH",
                dest="paths",
                help=(
                    "a file the change touches; repeatable. A path can raise the "
                    "level on its own"
                ),
            )
            subparser.add_argument(
                "--json", action="store_true", dest="as_json",
                help="emit the decision as JSON instead of prose",
            )
        if name == "init":
            subparser.add_argument(
                "--harness-memory",
                metavar="PATH",
                help=(
                    "make PATH a move-proof symlink to this project's "
                    f"{lint.DEFAULT_MEMORY_DIR}/ directory"
                ),
            )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return validate.run(args.path, stdout=sys.stdout, stderr=sys.stderr)
    if args.command == "derive":
        return derive.run(
            args.path, args.check, stdout=sys.stdout, stderr=sys.stderr
        )
    if args.command == "lint":
        return lint.run(args.path, stdout=sys.stdout, stderr=sys.stderr)
    if args.command == "probe":
        return probe.run(args.path, stdout=sys.stdout, stderr=sys.stderr)
    if args.command == "route":
        return route.run(
            args.description, args.paths, args.as_json, stream=sys.stdout
        )
    return init.run(args.harness_memory, stdout=sys.stdout, stderr=sys.stderr)

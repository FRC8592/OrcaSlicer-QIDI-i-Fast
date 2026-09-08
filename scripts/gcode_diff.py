#!/usr/bin/env python3
"""Diff a sliced G-code file against a QIDI Print reference export.

Implements the four comparisons the handoff asks for — start block, end block,
temperature commands, M-codes used — plus a fifth for the dual-extruder case,
the tool-change sequence.  Coordinates and comments are ignored where the
handoff says to ignore them, and *not* ignored inside the start and end blocks,
which are our own verbatim strings and whose comments carry meaning.

Every difference found is reported.  scripts/accepted.py decides whether a
difference is a known, justified deviation or an unexpected one; it never
decides whether it is printed.
"""

import argparse
import difflib
import os
import re
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import accepted  # noqa: E402

# OrcaSlicer appends its whole resolved configuration as comments after the
# G-code proper; it is not machine-directed and would swamp every comparison.
CONFIG_TRAILER = "; CONFIG_BLOCK_START"
# Cap on raw unified-diff lines shown; every difference still gets an
# itemised, classified entry below the diff.
DIFF_CAP = 40

START_FIRST, START_LAST = ";T0", "M141 S0"
END_FIRST, END_LAST = "M107 T-2", ";End of Gcode"

TEMPERATURE = re.compile(r"^(M104|M109|M140|M190|M141|M191)\b")
# Numeric arguments that are positions, distances or feedrates — the things the
# handoff means by "coordinates".  S/P/R/T are left alone: they carry the
# temperatures, fan speeds and tool indices the comparison is actually about.
COORD = re.compile(r"(?<=[XYZEABFIJ])-?\d*\.?\d+")
CODE = re.compile(r"^([GM]\d+|T-?\d+)")
# Codes whose argument forms are worth enumerating.  G0/G1 are excluded: they
# are toolpath and produce thousands of distinct shapes.
FORM_CODES = re.compile(r"^(M\d+|G(?:21|28|90|91|92)|T-?\d+)\b")
OBJECT_ID = re.compile(r"(?<=id:)\d+")


def load(path):
    """Read a G-code file as a list of lines, CRLF-normalised, trailer removed."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = [line.rstrip("\r\n") for line in fh]
    for i, line in enumerate(lines):
        if line.startswith(CONFIG_TRAILER):
            return lines[:i]
    return lines


def block(lines, first, last, label, path):
    try:
        i = lines.index(first)
    except ValueError:
        sys.exit("%s: cannot find %r, which starts the %s" % (path, first, label))
    for j in range(i, len(lines)):
        if lines[j] == last:
            return i, j, lines[i:j + 1]
    sys.exit("%s: found %r but not the closing %r of the %s"
             % (path, first, last, label))


def strip_comment(line):
    return re.sub(r"\s*;.*$", "", line).strip()


def norm_coords(line):
    # OrcaSlicer's "; printing object <name> id:<n>" marker carries a
    # pointer-derived id that changes between runs; collapse it so the report is
    # reproducible.
    return OBJECT_ID.sub("<id>", COORD.sub("<n>", line)).strip()


def norm_temps(line):
    return re.sub(r"(?<=S)-?\d*\.?\d+", "<t>", line)


class Report:
    """Collects difference items and renders them, classified but never hidden."""

    def __init__(self, context=None):
        self.context = context
        self.sections = []
        self.accepted = 0
        self.known = 0
        self.unexpected = 0

    def section(self, title, note=None):
        self.sections.append({"title": title, "note": note, "items": [], "raw": []})
        return self.sections[-1]

    def raw(self, section, text):
        section["raw"].append(text)

    def add(self, section, kind, side, text, detail=None):
        verdict = accepted.classify(kind, side, text, self.context)
        if verdict and accepted.is_known(verdict[0]):
            self.known += 1
        elif verdict:
            self.accepted += 1
        else:
            self.unexpected += 1
        section["items"].append({"side": side, "text": text,
                                 "detail": detail, "verdict": verdict})

    def render(self):
        out = []
        for sec in self.sections:
            out.append("### " + sec["title"])
            out.append("")
            if sec["note"]:
                out.append(sec["note"])
                out.append("")
            for raw in sec["raw"]:
                out.append(raw)
            if not sec["items"]:
                if not sec["raw"]:
                    out.append("No differences.")
                    out.append("")
                continue
            unexpected = [i for i in sec["items"] if not i["verdict"]]
            known = [i for i in sec["items"]
                     if i["verdict"] and accepted.is_known(i["verdict"][0])]
            acc = [i for i in sec["items"]
                   if i["verdict"] and not accepted.is_known(i["verdict"][0])]
            if unexpected:
                out.append("**UNEXPECTED (%d)**" % len(unexpected))
                out.append("")
                for item in unexpected:
                    out.append("- `%s` %s%s" % (
                        item["text"], _side_word(item["side"]),
                        (" — " + item["detail"]) if item["detail"] else ""))
                out.append("")
            for label, group in (("KNOWN", known), ("ACCEPTED", acc)):
                if not group:
                    continue
                seen = set()
                out.append("<details><summary>%s (%d)</summary>" % (label, len(group)))
                out.append("")
                for item in group:
                    key = (item["text"], item["side"])
                    if key in seen:
                        continue
                    seen.add(key)
                    name, reason, source = item["verdict"]
                    out.append("- `%s` %s%s — **%s**: %s (%s)" % (
                        item["text"], _side_word(item["side"]),
                        (" — " + item["detail"]) if item["detail"] else "",
                        name, reason, source))
                out.append("")
                out.append("</details>")
                out.append("")
        return "\n".join(out)


def _side_word(side):
    return {"ref": "*(reference only)*", "ours": "*(ours only)*"}.get(side, "")


# --------------------------------------------------------------------------
# checks

def check_block(report, kind, title, ref, ours, first, last, ref_path, our_path, note):
    _, _, rb = block(ref, first, last, title, ref_path)
    _, _, ob = block(ours, first, last, title, our_path)
    sec = report.section(title, note)
    if rb == ob:
        report.raw(sec, "Byte-identical (%d lines)." % len(rb))
        report.raw(sec, "")
        return
    diff = list(difflib.unified_diff(rb, ob, "reference", "ours", lineterm="", n=1))
    report.raw(sec, "```diff")
    report.raw(sec, "\n".join(diff))
    report.raw(sec, "```")
    report.raw(sec, "")
    # Report each changed line as its own item so it can be classified.
    for line in diff[2:]:
        if line.startswith("-") and not line.startswith("---"):
            report.add(sec, kind, "ref", line[1:])
        elif line.startswith("+") and not line.startswith("+++"):
            report.add(sec, kind, "ours", line[1:])
    # A structural comparison, so a temperature-value-only difference is
    # distinguishable from a real change in the block's shape.
    if [norm_temps(x) for x in rb] == [norm_temps(x) for x in ob]:
        report.raw(sec, "With S-values normalised the two blocks are identical, so "
                        "every difference above is a temperature value, not a "
                        "structural change.")
        report.raw(sec, "")


def check_temperatures(report, ref, ours):
    sec = report.section("Temperature commands",
                         "Every `M104` / `M109` / `M140` / `M190` / `M141` / `M191` "
                         "line in the whole file, in order.")
    rt = [l.strip() for l in ref if TEMPERATURE.match(l.strip())]
    ot = [l.strip() for l in ours if TEMPERATURE.match(l.strip())]
    if rt == ot:
        report.raw(sec, "Identical sequence (%d commands)." % len(rt))
        report.raw(sec, "")
        return
    diff = list(difflib.unified_diff(rt, ot, "reference", "ours", lineterm="", n=0))
    report.raw(sec, "```diff")
    if len(diff) > DIFF_CAP:
        report.raw(sec, "\n".join(diff[:DIFF_CAP]))
        report.raw(sec, "... %d more diff lines elided; the table below is the "
                        "complete summary." % (len(diff) - DIFF_CAP))
    else:
        report.raw(sec, "\n".join(diff))
    report.raw(sec, "```")
    report.raw(sec, "")
    rc, oc = Counter(rt), Counter(ot)
    rows = []
    for form in sorted(set(rc) | set(oc)):
        if rc[form] != oc[form]:
            rows.append((form, rc[form], oc[form]))
    if rows:
        report.raw(sec, "| command | reference | ours |")
        report.raw(sec, "|---|---:|---:|")
        for form, a, b in rows:
            report.raw(sec, "| `%s` | %d | %d |" % (form, a, b))
        report.raw(sec, "")
    for form, a, b in rows:
        side = "ref" if b == 0 else ("ours" if a == 0 else None)
        report.add(sec, "temperature", side, form,
                   "reference %d, ours %d" % (a, b))


def census(lines):
    bare, forms = Counter(), Counter()
    for line in lines:
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        m = CODE.match(line)
        if not m:
            continue
        bare[m.group(1)] += 1
        if FORM_CODES.match(line):
            # M4010's hex payload is unique per chunk; collapse it or the census
            # reports 131 distinct "forms" of one command.
            if line.startswith("M4010"):
                forms["M4010 <payload>"] += 1
            else:
                forms[norm_coords(strip_comment(line))] += 1
    return bare, forms


def check_census(report, ref, ours):
    rb, rf = census(ref)
    ob, of = census(ours)
    sec = report.section("M-codes and G-codes used",
                         "Level 1 is the bare code inventory; level 2 enumerates "
                         "argument forms for M-codes and control G-codes only "
                         "(`G0`/`G1` are toolpath and excluded from level 2).")
    for label, r, o, kind in (("Code inventory", rb, ob, "census"),
                              ("Argument forms", rf, of, "census")):
        report.raw(sec, "**%s**" % label)
        report.raw(sec, "")
        report.raw(sec, "| form | reference | ours |")
        report.raw(sec, "|---|---:|---:|")
        for form in sorted(set(r) | set(o)):
            a, b = r.get(form, 0), o.get(form, 0)
            mark = "" if a == b else "  **≠**"
            report.raw(sec, "| `%s` | %d | %d |%s" % (form, a, b, mark))
        report.raw(sec, "")
    for form in sorted(set(rb) | set(ob)):
        a, b = rb.get(form, 0), ob.get(form, 0)
        if a == b:
            continue
        side = "ref" if b == 0 else ("ours" if a == 0 else None)
        report.add(sec, "census", side, form, "reference %d, ours %d" % (a, b))


def toolchanges(lines):
    """Distinct normalised tool-change windows in the print body, with counts."""
    _, end, _ = block(lines, START_FIRST, START_LAST, "start block", "<file>")
    variants, positions = Counter(), []
    for k in range(end + 1, len(lines)):
        if re.fullmatch(r"T[01]", lines[k].strip()):
            positions.append(k + 1)
            window = lines[max(0, k - 3):k + 5]
            variants["\n".join(norm_coords(x) for x in window)] += 1
    return variants, positions


def check_toolchanges(report, ref, ours):
    rv, rpos = toolchanges(ref)
    ov, opos = toolchanges(ours)
    sec = report.section(
        "Tool-change sequence",
        "Every bare `T0` / `T1` in the print body (the start block's prime pair is "
        "excluded), with three lines before and four after, coordinates normalised, "
        "grouped into distinct variants.")
    report.raw(sec, "Reference: %d body tool changes in %d distinct shapes. "
                    "Ours: %d in %d." % (len(rpos), len(rv), len(opos), len(ov)))
    report.raw(sec, "")
    if not opos:
        report.raw(sec, "**No body tool change was emitted at all — the comparison "
                        "below is vacuous and this run must be treated as a "
                        "failure, not a pass.**")
        report.raw(sec, "")
        report.add(sec, "toolchange", "ref", "(no tool change emitted)",
                   "the slice produced no body T0/T1")
        return
    for label, variants in (("reference", rv), ("ours", ov)):
        report.raw(sec, "**%s**" % label)
        report.raw(sec, "")
        for text, count in variants.most_common():
            report.raw(sec, "```gcode")
            report.raw(sec, "; x%d" % count)
            report.raw(sec, text)
            report.raw(sec, "```")
        report.raw(sec, "")
    # Compare each of our variants against its closest reference variant.
    for text, count in ov.most_common():
        best = max(rv, key=lambda r: difflib.SequenceMatcher(
            None, r.split("\n"), text.split("\n")).ratio())
        diff = list(difflib.unified_diff(best.split("\n"), text.split("\n"),
                                         "closest reference variant", "ours",
                                         lineterm="", n=0))
        for line in diff[2:]:
            if line.startswith("-") and not line.startswith("---"):
                report.add(sec, "toolchange", "ref", line[1:])
            elif line.startswith("+") and not line.startswith("+++"):
                report.add(sec, "toolchange", "ours", line[1:])


def _rel(path):
    return os.path.relpath(os.path.abspath(path), REPO)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("reference")
    ap.add_argument("ours")
    ap.add_argument("--title", default="Comparison")
    ap.add_argument("--context", choices=("single", "dual"), default=None,
                    help="which comparison this is; scopes the accepted registry")
    ap.add_argument("--toolchange", action="store_true",
                    help="also compare the tool-change sequence (dual case)")
    ap.add_argument("-o", "--output", help="write the report here as well as stdout")
    args = ap.parse_args()

    ref, ours = load(args.reference), load(args.ours)
    report = Report(args.context)

    check_block(report, "start_block", "Start block", ref, ours,
                START_FIRST, START_LAST, args.reference, args.ours,
                "`%s` through `%s` inclusive, compared literally: this block is our "
                "own `machine_start_gcode` verbatim and its comments carry meaning."
                % (START_FIRST, START_LAST))
    check_block(report, "end_block", "End block", ref, ours,
                END_FIRST, END_LAST, args.reference, args.ours,
                "`%s` through `%s` inclusive, compared literally."
                % (END_FIRST, END_LAST))
    check_temperatures(report, ref, ours)
    check_census(report, ref, ours)
    if args.toolchange:
        check_toolchanges(report, ref, ours)

    body = "\n".join([
        "## " + args.title, "",
        "- reference: `%s`" % _rel(args.reference),
        "- ours: `%s`" % _rel(args.ours),
        "- **%d accepted, %d known-unresolved, %d unexpected**"
        % (report.accepted, report.known, report.unexpected),
        "", report.render()])
    sys.stdout.write(body + "\n")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(body + "\n")
    return 1 if report.unexpected else 0


if __name__ == "__main__":
    sys.exit(main())

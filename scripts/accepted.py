#!/usr/bin/env python3
"""Registry of differences from the QIDI Print reference that are known and accepted.

This file changes a difference's *classification*, never its visibility: every
entry the harness finds is printed in the report either way.  An ACCEPTED entry
carries its reason and the document that justifies it; anything not matched here
is UNEXPECTED and fails the run.  Hard rule 7 (CLAUDE.md) — "report every
difference, do not suppress diffs to make a check pass" — means nothing may be
added here without a written justification that already exists in TODO.md,
README.md or reference/extracted-gcode.md.

Each rule is matched against a single difference item:

  kinds    which checks it applies to (start_block, end_block, temperature,
           census, motion, toolchange, priming); empty means all
  contexts which comparison it applies to ("single", "dual"); empty means both.
           This is what keeps a fixture artifact from becoming a blanket excuse:
           the dual comparison's second filament is OrcaSlicer's stock
           `Qidi Generic PETG`, so it legitimately brings its own pressure
           advance and bed temperature, but the same lines appearing in the
           single-extruder slice would be a real defect in our own profile.
  side     "ref"  the line exists only in the QIDI Print reference
           "ours" the line exists only in our slice
           None   either
  pattern  regex matched against the difference text.  Temperature lines are
           matched in canonical form (comment stripped, `T` before `S`).

Things that are deliberately *absent* from this registry, so that their
reappearance fails the run: the M201/M203/M204/M205 machine-limit preamble and
the per-feature M204/M205, OrcaSlicer's spiral Z lift (G2/G3/G17 or a Z change
per retraction), any travel feedrate above the reference's, and a non-zero
retract debt at a tool change.  All were removed or ruled out by the first-print
review (2026-09-07); see TODO.md "Decided".

The first dual print (2026-09-12, failed) retired four entries: the 2 mm
tool-change retract, ooze prevention's second M109, its "; removed M104", and
our M109 firing in both directions.  All four described behaviour the rewritten
change_filament_gcode no longer has.  Nothing was added in their place, because
no dual slice has been produced since the rewrite -- the 2.4.2 CLI cannot slice
two filaments and there is no fallback slicer on macOS.  **The next dual run
will therefore report differences this registry has never seen**, including the
park move our block emits where the reference parks with a Y as well.  That is
the intended failure mode: judge them against the reference, then register the
deliberate ones.  See TODO.md "Found by the first dual print".
"""

import re

Rule = tuple  # (name, kinds, contexts, side, pattern, reason, source)

RULES = [
    # ---- things OrcaSlicer structurally cannot emit ---------------------------
    ("m4010-thumbnail", (), (), "ref", r"^M4010\b",
     "QIDI Print's display preview blob; OrcaSlicer has no equivalent.",
     "extracted-gcode.md §6"),
    ("m2100-time-estimate", (), (), "ref", r"^M2100\b",
     "Print-time estimate handed to the QIDI display; OrcaSlicer has no equivalent.",
     "extracted-gcode.md §6"),
    ("cura-setting-trailer", (), (), "ref", r"^;SETTING_3",
     "Cura's embedded quality profile; not machine-directed.",
     "extracted-gcode.md §4"),

    # ---- things OrcaSlicer adds that the reference has not --------------------
    ("force-resume-fan-speed", (), (), "ours", r"^;_FORCE_RESUME_FAN_SPEED$",
     "OrcaSlicer appends this after change_filament_gcode to re-assert fan speed.",
     "CLAUDE.md 'How Orca actually emits a tool change', step 3"),

    # ---- the tool change: deliberate omissions from change_filament_gcode -----
    ("commented-m105", (), (), "ref", r"^;M105$",
     "Commented-out temperature report in reference variants A and C; omitted.",
     "TODO.md 'Accepted diffs for task 6 introduced by task 3'"),
    ("cura-preheat-ramp", (), (), "ref", r"^M104 T[01] S(0|155\.4|168\.3)$",
     "Cura's interpolated preheat ramp (intermediate setpoints on the way back "
     "from 150 C) and its final M104 T0 S0 when a tool is finished with. "
     "OrcaSlicer preheats in one step. (The 150 C standby drop was reproduced by "
     "ooze_prevention + idle_temperature between 2026-09-07 and 2026-09-20; it "
     "is a difference again — see standby-drop-not-reproduced.)",
     "TODO.md 'Found by the first dual print', extracted-gcode.md §7"),
    ("toolchange-fan-speed", ("toolchange", "census"), (), None, r"^M10[67]\b",
     "Fan speed is a filament/process property OrcaSlicer owns; the reference's "
     "per-extruder Cura fan curve is out of scope for a single-PLA profile.",
     "TODO.md 'Accepted diffs', extracted-gcode.md §7 'Fan speeds'"),
    # ---- value-only differences that track the fixture, not the profile -------
    ("t1-heating-temperature", ("start_block", "temperature"), (), None,
     r"^;?M10[49] T1 S\d+(\.\d+)?$",
     "The T1 heating pair. Its value tracks whatever filament sits in extruder 2 "
     "and nothing else: the reference's second slot held PETG at 230 C, ours holds "
     "PLA at 200 C (single case, where the lines are commented out and the machine "
     "ignores them) or the stock Qidi Generic PETG at 240 C (dual case). The block "
     "is otherwise identical, which the S-normalised comparison confirms.",
     "TODO.md task 3, README.md 'Values from the reference G-code'"),

    # ---- artifacts of the dual-extruder test fixture, not of the profile -----
    # The dual comparison's second filament is OrcaSlicer's stock Qidi Generic
    # PETG, used as a fixture. It brings its own settings, and the reference's
    # own second material was a different PETG. None of these rules apply to the
    # single-extruder comparison, where the same lines would be real defects.
    ("fixture-pressure-advance", (), ("dual",), "ours", r"^M900\b",
     "FIXTURE: the stock Qidi Generic PETG in slot 2 leaves enable_pressure_advance "
     "on, so OrcaSlicer emits M900. Our own filament preset sets it to 0 and the "
     "single-extruder comparison confirms zero M900 there.",
     "TODO.md task 5 'enable_pressure_advance'"),
    ("fixture-bed-temperature", (), ("dual",), None,
     r"^M1[49]0 S\d+( ; set bed temperature)?$",
     "FIXTURE: the stock Qidi Generic PETG's cool_plate_temp is 60 C against our "
     "PLA's 80 C, so a mixed job emits an extra bed command. This is the "
     "bed_temperature_formula question, already deferred until a second material "
     "actually ships; every filament preset this repo ships says 80.",
     "TODO.md 'Deferred until a second material exists'"),
    ("fixture-toolchange-count", ("census",), ("dual",), None, r"^T[01]$",
     "FIXTURE: the number of tool changes is a property of the test model (two "
     "cubes alternating every layer), not of the profile. What matters is that "
     "body tool changes are emitted and that their shape matches; see the "
     "tool-change check.",
     "task 6"),
    ("fixture-toolchange-temperature", ("toolchange", "temperature"), ("dual",), None,
     r"^M109 S(2[34]0|250)$",
     "FIXTURE: the temperature our change_filament_gcode blocks on is the incoming "
     "filament's. The reference's T1 held a 230 C PETG; the fixture's holds the "
     "stock Qidi Generic PETG at 240/250 C.",
     "extracted-gcode.md §7"),
    ("toolpath-speeds", ("motion",), ("dual",), None, r"^printing: max F: .*",
     "FIXTURE: per-feature print speeds are inherited from the stock @Qidi XMax "
     "process and deliberately not converted from Cura (task 4). The "
     "reference's PLA walls/infill run at 30/60 mm/s, exactly ours — the "
     "single-extruder comparison must show equal maxima — but its PETG job "
     "printed at 25/50 mm/s, which no profile in this repo describes.",
     "README.md 'Process profiles'"),

    # ---- OrcaSlicer's own bookkeeping comments -------------------------------
    ("orca-bookkeeping-comments", ("toolchange",), (), "ours",
     r"^;(WIPE_(START|END)|LAYER_CHANGE|Z:|HEIGHT:|TYPE:|_SET_FAN_SPEED|AFTER_LAYER|"
     r"BEFORE_LAYER)|^; (printing object|stop printing object)",
     "OrcaSlicer's own G-code markers, which land inside the tool-change window. "
     "They are comments, not machine commands, and QIDI Print has no equivalent.",
     "task 6 ('ignoring ... comments')"),

    # ---- OrcaSlicer's tool-change temperature scheduling ---------------------
    ("standby-drop-not-reproduced", ("temperature", "census", "toolchange"),
     ("dual",), "ref", r"^M104 T[01] S\d+$",
     "The reference parks the idle hotend at 150 C and ramps it back; we no "
     "longer do. ooze_prevention was turned off on 2026-09-20 because its "
     "post_toolchange emitted a second blocking M109 on top of the one in "
     "change_filament_gcode, and the failing dual print spent most of its wall "
     "clock waiting. The standby drop is recoverable without that cost, by "
     "putting the reference's own M104 S150 T<previous> inside the block — open "
     "in TODO.md, not done.",
     "TODO.md 'Found by the first dual print', extracted-gcode.md §7"),

    # ---- differences that are documented but NOT yet resolved -----------------
    # These are in TODO.md awaiting a decision. They are listed under KNOWN in
    # the report, never hidden, and they do not fail the run — a *new* difference
    # does. Removing an entry from here is how a resolved question gets retired.
    ("orca-g92-e-resets", ("census",), (), None, r"^G92$",
     "OrcaSlicer emits G92 E0 after every retraction; QIDI Print's absolute E "
     "climbs monotonically and only resets in the start and end blocks. "
     "Functionally equivalent under M82, structurally very different.",
     "TODO.md 'Found by task 6'"),
    ("orca-preamble-codes", ("census", "toolchange"), (), None,
     r"^(G21|G90|M82( ; use absolute distances for extrusion)?)$",
     "OrcaSlicer writes its own G21 (mm), G90 (absolute positioning) and a second "
     "M82 after our start block. The reference has neither G21 nor G90 and only "
     "the M82 our own block emits. Harmless on a Marlin machine, but unverified "
     "on the i-Fast's Chitu board.",
     "TODO.md 'Found by task 6'"),
    ("cura-midprint-temperature-reassert", ("temperature", "census"), (),
     None, r"^M104( S200)?$",
     "QIDI Print re-asserts M104 S200 once mid-print, at the same value the start "
     "block already set. OrcaSlicer does not. No behavioural difference is "
     "expected, but it is unexplained.",
     "TODO.md 'Found by task 6'"),
    ("fixture-bed-command-count", ("census",), ("dual",), None, r"^M140$",
     "One extra M140, from the PETG fixture's 60 C cool-plate temperature. See "
     "fixture-bed-temperature.",
     "TODO.md 'Deferred until a second material exists'"),

    # ---- toolpaths -----------------------------------------------------------
    ("toolpath-moves", ("census", "toolchange"), (), None, r"^G[01]\b",
     "Travel and extrusion move counts and coordinates: different slicer, "
     "different toolpaths. Explicitly out of scope per the task brief's 'ignoring "
     "coordinates'.",
     "task 6, extracted-gcode.md §8 'Accepted diffs for task 6'"),
]

# Rules whose subject is documented in TODO.md but *not settled*. They are
# reported under KNOWN rather than ACCEPTED and, like ACCEPTED, do not fail the
# run; the point of the distinction is that this set should shrink over time.
KNOWN = {
    "orca-g92-e-resets",
    "orca-preamble-codes",
    "cura-midprint-temperature-reassert",
    "toolchange-retract-prime",
    "cura-preheat-ramp",
    "orca-standby-schedule",
    "ooze-post-toolchange-wait",
}


def is_known(rule_name):
    return rule_name in KNOWN


_COMPILED = [(name, kinds, contexts, side, re.compile(pat), reason, source)
             for name, kinds, contexts, side, pat, reason, source in RULES]


def classify(kind, side, text, context=None):
    """Return (rule_name, reason, source) if this difference is accepted, else None."""
    text = text.strip()
    for name, kinds, contexts, rule_side, pattern, reason, source in _COMPILED:
        if kinds and kind not in kinds:
            continue
        if contexts and context not in contexts:
            continue
        if rule_side is not None and rule_side != side:
            continue
        if pattern.search(text):
            return (name, reason, source)
    return None

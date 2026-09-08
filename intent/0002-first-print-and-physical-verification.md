# Intent: first print, and the questions only the machine can answer
Author: Brad Sneade. Status: **open**.

## Problem

The profile is written, packaged, and validated against QIDI Print's exports by a
repeatable harness — and **nothing has been printed with it**. Every claim in
[`README.md`](../README.md) is a claim about G-code, not about a machine.

Three behaviours cannot be settled by reading or diffing G-code at all, because they are
firmware and hardware behaviour that the file only triggers:

- **A redundant bare `T0` before layer 1.** The 2.4.2 GUI emits one between the start
  block's prime line and the first layer; neither QIDI Print nor a CLI slice does. T0 is
  already the active tool, so it *should* be a no-op — but head auto-lift is firmware
  behaviour triggered by tool changes, and nobody has watched what this firmware does
  with a tool change to the tool it is already on.
- **`M106 T-2 S255`.** The profile reproduces it at layer 1 because the reference does.
  `T-2` is not an extruder index and nothing in QIDI's published profiles says what it
  addresses. Chamber circulation, exhaust, and a side blower are all plausible, and the
  answer changes whether the command matters for PLA overhangs or for the enclosure.
- **Which head assembly is installed** — standard brass, or the 350 °C high-temp variant.
  The reference never exceeds 230 °C, so the G-code cannot distinguish them.

## Proposed outcome

One clean supervised print off this profile, and each of the three questions answered by
watching the machine rather than by inference.

The print itself is the point: it either validates a profile that is currently
theoretical, or it produces the first real evidence of what is wrong with it.

## Affected users and systems

The physical i-Fast, with a human in front of it. [`profiles/`](../profiles/), if the
print turns up something that needs changing. [`TODO.md`](../TODO.md), which is where the
answers get recorded.

## Constraints

- **Single extruder, PLA, small model, supervised, chamber heater off.** The original
  brief's closing instruction, carried into
  [`0001`](0001-orcaslicer-profile-for-the-ifast.md) §"How the work was decomposed":
  get that clean before trusting anything else in the repo.
- **Hard rule 8** ([`CLAUDE.md`](../CLAUDE.md) §"Hard rules"): ask about the physical
  machine, don't guess. That rule is the reason this intent exists as a separate piece of
  work instead of being closed out from a desk.
- The redundant `T0` is **not** fixable by editing the start block if it turns out to
  misbehave — OrcaSlicer emits it afterwards, from its own code path. Any fix is a
  different shape of change.

## Open questions

The three above, tracked live as checkboxes in [`TODO.md`](../TODO.md) §"Open questions
for the human" — that file stays the record and is where they get ticked. Listed here for
scope only, deliberately not duplicated:

- First print: watch for a lift/park cycle before the first layer.
- First print: which fan comes on as layer 1 starts?
- Which head assembly is installed.

Out of scope until this is done, per [`README.md`](../README.md) §Scope: tuned
retraction, flow calibration, pressure advance, per-material profiles, chamber-temperature
workflows, and nozzle sizes other than 0.4.

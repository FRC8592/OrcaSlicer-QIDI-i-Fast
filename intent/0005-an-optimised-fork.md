# Intent: a second profile that is tuned rather than faithful
Author: Brad Sneade. Status: **draft**.

> Asked for on 2026-09-26, while the factory-faithful profile was still being debugged,
> and written down on 2026-10-01 at the originator's request. **Still a draft**: the
> words below are assembled from what was said in the session and from findings this
> project has already made, not written fresh by the originator. Rewrite the Problem and
> Proposed outcome in your own words before starting — the rest is raw material.
>
> Gated on [`0004`](0004-make-the-dual-extruder-print-work.md) landing a good dual print.

## Problem

[`profiles/`](../profiles/) exists to reproduce what QIDI Print does on this machine.
That is the whole point of it, and
[hard rule 1](../CLAUDE.md#hard-rules-do-not-relax-these) — derive, don't invent — is what
keeps it honest. Every value traces to QIDI's own output, the base OrcaSlicer preset, or
QIDI's published profiles, and the harness in [`scripts/`](../scripts/) exists to prove it.

But faithful is not the same as good. QIDI Print is Cura 4.9.1 driving a 2021 machine, and
this project has repeatedly found places where the reference's behaviour is a historical
artifact rather than a requirement — and has had to ship the artifact anyway, because the
alternative would have been an invented value. A profile aimed at *printing well* cannot
live under that rule, and so cannot live in these files.

The machine also has capability nobody has used: OrcaSlicer has a decade of features Cura
4.9.1 did not, and the only reason this profile declines them is fidelity.

## Proposed outcome

A second profile — same machine, same geometry, same hard rules about the firmware
(auto-lift, extruder offsets, no network config) — chosen for print quality and print
time instead of for matching a reference. Good enough looks like: it beats the faithful
profile on a part I actually care about, and I can say why each difference is there.

It has to be a fork rather than a branch of the same files, because the two answer
different questions and `profiles/` must stay auditable against
[`reference/extracted-gcode.md`](../reference/extracted-gcode.md).

## Affected users and systems

Me, and anyone who wants this machine to print well rather than to print like 2021. New
preset files; the existing ones untouched. The validation harness does **not** transfer —
it is built on the premise that differences from the reference are defects, which is the
opposite of this profile's premise. It gets its own expectations, or none.

## Constraints

- Firmware rules still apply in full:
  [4](../CLAUDE.md#hard-rules-do-not-relax-these) (auto-lift),
  [5](../CLAUDE.md#hard-rules-do-not-relax-these) (extruder offsets stay zero),
  [3](../CLAUDE.md#hard-rules-do-not-relax-these) (no network config).
  These are properties of the machine, not of the reference.
- [Hard rule 6](../CLAUDE.md#hard-rules-do-not-relax-these) (don't raise motion limits)
  needs an explicit decision rather than silent relaxation — it is a safety limit, and
  QIDI's own `machine_max_acceleration_e = 10000` is already higher than what we ship.
- [Hard rule 8](../CLAUDE.md#hard-rules-do-not-relax-these) — ask before guessing about
  the physical machine — is if anything more important here, not less.
- Hard rule 1 is the one that is deliberately **not** inherited. Say so out loud in the
  fork's own README, or someone will file a bug about it.

## Open questions

The candidate list, with the evidence that raised each, lives in
[`TODO.md`](../TODO.md) under *Planned: an optimised fork*. Short version: symmetric
standby, the prime tower ([`0006`](0006-a-prime-tower-for-the-fork.md)), travel Z-hop,
`ooze_prevention` with its preheat backtrace, the fan curve, brim and object spacing, and
the tuning the original brief put out of scope — pressure advance, flow, retraction.

Two findings worth carrying in from the factory two-cube exports (2026-10-01,
[§10](../reference/extracted-gcode.md)): QIDI's own ooze prevention costs **3.4× the wall
clock** on a two-object plate, and its prime tower costs **1.6×**. Neither is free, and the
fork has to decide what it is buying.

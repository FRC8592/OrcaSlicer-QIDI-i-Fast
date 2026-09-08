# Intent: an OrcaSlicer profile for the QIDI i-Fast
Author: Brad Sneade. Status: **delivered** (2026-09-07).

> Written retroactively on 2026-09-08 by extracting the intent half of
> [`ifast-orca-profile-handoff.md`](../ifast-orca-profile-handoff.md), which predates
> this convention and fuses intent with design. **The handoff is still the authoritative
> spec** — its seven tasks, hard rules and definition of done all live there. This file
> records only what was wanted and why, before any of that was decided.

## Problem

OrcaSlicer ships no profile for the QIDI i-Fast, so the machine cannot be sliced from
Orca at all — it is driven by QIDI Print, a Cura 4.9.1 fork.

Orca *does* ship profiles for the i-Fast's siblings — X-Plus, X-Max and X-CF Pro — which
share the Chitu-derived board, the firmware and the G-code conventions. The trap is the
brand overlap: QIDI's current machines (X-Max 3, X-Plus 3, Q1, Plus 4) are a completely
different Klipper generation, and their profiles look authoritative while being wrong for
this machine in every way that matters.

## Proposed outcome

A small git repo holding machine, process and minimal filament JSONs that Orca loads
without warnings, showing the i-Fast at its true 330 × 250 × 320 mm — plus a record of
where every value came from and a list of what still needs eyes on the machine.

Every value derived from the legacy base profile, QIDI's own published profiles, or
QIDI Print's reference exports. Nothing invented, and nothing plausible-looking borrowed
from another printer.

## Affected users and systems

The physical i-Fast (~2021: enclosed, dual Z, two independent hotends, firmware-managed
head auto-lift, heated chamber). OrcaSlicer 2.4.2, installed as the flatpak
`com.orcaslicer.OrcaSlicer`. The `Qidi X-Max 0.4 nozzle` → `fdm_qidi_common` →
`fdm_machine_common` preset chain it derives from. QIDI Print's exports in
[`reference/`](../reference/), which are the ground truth for machine behaviour.

## Constraints

The eight hard rules, one line each — the full statements are in
[`CLAUDE.md`](../CLAUDE.md) §"Hard rules", and that is the version that governs:

1. Derive, don't invent — no source means a `TODO(verify)`, not a default.
2. Never source values from the Klipper-generation QIDI machines.
3. No network or print-host configuration; the i-Fast speaks a proprietary UDP protocol.
4. Don't touch the firmware auto-lift; the slicer only emits `T0` / `T1`.
5. Extruder offsets stay zero — the firmware applies them.
6. Don't raise motion limits. This is not a fast machine.
7. Report every diff during validation; never suppress one to make a check pass.
8. Ask before guessing about the physical machine.

Also: target OrcaSlicer 2.4.2 specifically, since profiles are version-sensitive.

## Open questions

All resolved during the work. Each is recorded with its reasoning in
[`TODO.md`](../TODO.md) §Decided:

- Which legacy sibling to derive from → **`Qidi X-Max 0.4 nozzle`**, over the X-CF Pro.
- Which Orca version to target → **2.4.2**.
- Bed temperature, where QIDI's own `.ini` says 60 °C and the reference G-code says 80 →
  **80 °C**, the G-code wins.
- Whether the start block's prime-line `B` value is a constant → **no, conditional** on
  whether extruder 2 carries filament.
- Whether a prime/wipe tower is usable → **no**, it requires relative E on 2.4.2 and the
  reference is absolute-E.
- Which nozzle sizes to ship → **0.4 only**; it is the only size QIDI documents, and the
  process values for any other would have to be invented.

What is *not* resolved here is anything that needs the physical machine. That became its
own intent: [`0002-first-print-and-physical-verification.md`](0002-first-print-and-physical-verification.md).

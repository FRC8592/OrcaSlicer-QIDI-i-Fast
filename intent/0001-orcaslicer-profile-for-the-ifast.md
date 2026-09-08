# Intent: an OrcaSlicer profile for the QIDI i-Fast
Author: Brad Sneade. Status: **delivered** (2026-09-07).

> Written retroactively on 2026-09-08 from `ifast-orca-profile-handoff.md`, the original
> brief, which predated this convention and fused intent with design. That file was
> folded into this one and [`CLAUDE.md`](../CLAUDE.md) on 2026-09-08 and removed from the
> repository (and from its history) before publication. **This file is now the record of
> what was wanted, why, and how the work was broken up**; the hard rules and the
> definition of done live in `CLAUDE.md`, which governs.

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

## Inputs assumed present

The brief required all of these before any work started, and required stopping to ask
rather than proceeding on assumptions if one was missing:

1. `reference/single-extruder.gcode` — exported from QIDI Print for the i-Fast: simple
   model, one extruder, PLA. **The ground truth for machine behaviour.**
2. `reference/dual-extruder.gcode` — the same, but a two-material model forcing at least
   one tool change. Ground truth for the tool-change sequence.
3. QIDI's published legacy profile bundle for the i-Fast (PrusaSlicer `.ini`, Cura,
   Simplify3D `.fff`, ideaMaker) from the QIDI software page. Not redistributed in this
   repo — see [`../reference/qidi-profiles.md`](../reference/qidi-profiles.md).
4. A local clone of the OrcaSlicer repository.
5. The OrcaSlicer version the user is running, since profiles are version-sensitive.

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

## How the work was decomposed

Seven tasks, all delivered. `README.md`, `TODO.md` and `scripts/` cite them by number,
so the numbering is kept:

1. **Recon the schema.** Find the QIDI vendor profiles in the OrcaSlicer clone; write up
   which QIDI machines are present with their build volumes, the flattened `inherits`
   chain, what a user profile must look like for Orca to load it rather than silently
   reject it, and where user profiles live on Linux. Then pick the base — X-CF Pro or
   X-Max — and justify it. Never a Klipper-generation QIDI. → `CLAUDE.md` §"Recon results".
2. **Extract ground truth from the reference G-code.** Pull the start block, end block,
   chamber commands, heating order, every non-standard M-code, and the complete
   tool-change sequence out of the two exports **verbatim**, into
   `reference/extracted-gcode.md`. Use those blocks as-is: no tidying, no substituting
   equivalents from another printer.
3. **Build the machine profile.** From the chosen base, change only what the hardware
   demands: build volume 330 × 250 × 320, two extruders as a multi-tool printer, zero
   extruder offsets, temperatures for the standard brass head, the G-code blocks from
   task 2, and motion limits carried over unraised.
4. **Build process profiles.** 0.20 mm standard at minimum, more only if the base's
   structure made it trivial. Inherit speeds from the stock QIDI process rather than
   importing them from Cura, whose speed semantics do not map cleanly.
5. **Build a minimal filament profile.** One generic PLA inheriting Orca's, with temps
   from the QIDI reference. "Resist producing a full material library — that's tuning
   work that belongs after the machine is proven."
6. **Validate.** Work out the CLI invocation from `--help` rather than assuming flag
   names; slice a test model, diff the result against each reference ignoring coordinates
   and comments, and report every difference in the start block, end block, temperature
   commands and M-codes. Repeat for a two-material model. Suppressing a diff to make the
   check pass is forbidden — hard rule 7.
7. **Package.** The JSONs in a layout mapping onto Orca's user config dirs, Linux install
   instructions, a README documenting where every value came from and what is still
   unverified, `TODO.md`, and the AGPL-3.0 attribution chain back through Bambu Studio and
   PrusaSlicer.

The brief closed with an instruction that is not a task but a precondition on trusting
any of it: **the first print off this profile should be single extruder, PLA, a small
model, supervised, with the chamber heater off.** That became
[`0002-first-print-and-physical-verification.md`](0002-first-print-and-physical-verification.md).

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

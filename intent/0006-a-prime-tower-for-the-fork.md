# Intent: give the dual-extruder profile a prime tower
Author: Brad Sneade. Status: **draft**.

> Asked for on 2026-10-01, alongside [`0005`](0005-an-optimised-fork.md), after QIDI
> Print's own prime-tower export arrived. **Still a draft** — written from session
> findings rather than in the originator's words. Rewrite the Problem and Proposed
> outcome before starting.
>
> Belongs to the fork, not to [`profiles/`](../profiles/) — see Constraints.

## Problem

Every dual print this machine has produced has fought the same thing: a nozzle that has
been idle has to get back to printing pressure, and wherever that happens is where the
mess goes. The factory-faithful profile deals with it by retracting 10 mm, parking at the
bed edge and purging 8.5 mm there, which works but scatters strings across the plate on
every one of ~100 tool changes, and leaves a growing blob at `X0` and `X330`.

A prime tower is the normal answer: a small sacrificial column, printed layer by layer, so
every tool change ends by writing its purge into something solid, at the right height,
near the parts. The purge becomes structure instead of debris, and the nozzle arrives at
the part already at pressure.

Two things make it a real option now rather than a wish:

- **QIDI Print does it on this machine.** `reference/qp_2cube-mult-pt.gcode` has a
  29.6 mm square tower at `X150.2..179.8, Y90.0..119.6`, centred on `X165, Y105` — which
  is the same `Y104.805` lane QIDI already stages every tool change through, with or
  without a tower. The machine is not the obstacle.
- **The cost is known**: 126 min against the baseline's 81 for the same plate. Expensive,
  but roughly half what QIDI's ooze prevention costs (273 min), and unlike ooze prevention
  it puts the purge somewhere useful.

What stops it in `profiles/` is OrcaSlicer, not the printer. Turning `enable_prime_tower`
on makes 2.4.2 refuse the slice outright — *"The Wipe Tower is currently only supported
with the relative extruder addressing (use_relative_e_distances=1)"*, exit `-51`,
reproduced by the task-6 harness. Absolute E is a fidelity constraint carried from the
reference; a fork is free to drop it.

## Proposed outcome

A dual print where the purge ends up in a tower instead of on the bed and on the parts,
and where a tool change does not involve a 300 mm round trip to a bed edge. Good enough
looks like: both objects finish, the plate is clean of strings, and the time penalty is
one I am willing to pay for the result.

## Affected users and systems

The fork's machine and process presets. Specifically: `use_relative_e_distances`,
`enable_prime_tower` and the tower's own geometry settings, and
`change_filament_gcode` — which has to be re-derived, not carried over.

## Constraints

- **Relative E changes more than one key.** It changes every extrusion move in the output,
  so the existing harness's premise no longer holds; and it reroutes the tool change
  through `WipeTowerIntegration::append_tcr` (`v2.4.2:GCode.cpp:712`+), which processes
  `change_filament_gcode` itself with its own surrounding retraction and temperature
  handling. The block this project spent weeks getting right **does not carry over
  unexamined**.
- The start block's `A19` / `B19` prime line and the end block's `G92 E1` / `G1 E-1` mean
  different things under `M83`. Both need re-checking on the machine, not just re-reading.
- **Gate it behind a single-extruder relative-E smoke print** before any dual attempt. If
  the Chitu firmware mishandles `M83`, that is much cheaper to discover on one cube.
- Firmware rules unchanged: auto-lift untouched
  ([4](../CLAUDE.md#hard-rules-do-not-relax-these)), extruder offsets stay zero
  ([5](../CLAUDE.md#hard-rules-do-not-relax-these)).
- Tower placement must not sit where the parts do, and must not put the staging path
  across another object — the mistake of 2026-09-27, recorded in `TODO.md`.

## Open questions

- Does the i-Fast firmware actually honour `M83`? OrcaSlicer's own stock `fdm_qidi_common`
  start G-code emits it for sibling legacy machines, which is suggestive, not proof.
- Is Orca's tower placement controllable enough to land on QIDI's `X165, Y105` lane, and
  is that the right place anyway?
- Does a tower remove the need for the bed-edge park at all, or does the block still want
  a park for the standby drop?
- Live list in [`TODO.md`](../TODO.md) under *Planned: an optimised fork*.

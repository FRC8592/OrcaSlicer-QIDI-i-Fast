# Intent: make a two-head print come off the i-Fast in one piece
Author: Brad Sneade. Status: **open**.

> Written on 2026-09-20, after the first round of real prints from this profile.
> [`0002`](0002-first-print-and-physical-verification.md) got a single head printing;
> this is the half it deferred.

## Problem

Three prints on 2026-09-12, all sliced in OrcaSlicer 2.4.2 from
[`profiles/`](../profiles/):

| | file | result |
|---|---|---|
| 1 | one head | fine |
| 2 | both heads, two cubes, alternating every layer | failed |
| 3 | the other head | fine |

Each head works on its own. Put them together and the print sticks for a few layers,
goes soft and under-fed, and then comes off the plate and turns into spaghetti. The
plate ends up webbed with strings running clear off the edge. Photos are in
`Photos-1-001/`, grouped by timestamp; the G-code that produced them sits beside them.
Neither is committed — they are working files on my machine, and this repo does not carry
print evidence.

My first guess was that a head is not dropping all the way back down after a tool
change — it is the one part of this machine the slicer does not control, and it is the
obvious thing to suspect when single-head works and dual does not.

To find out whether the machine was even at fault, I printed
[`reference/dual-extruder.gcode`](../reference/dual-extruder.gcode) — QIDI Print's own
file for this machine — untouched. **It printed.** So the machine does dual prints
fine and the problem is in what we are generating.

It did come out stringy, and the two colours do not line up with each other. Whether
either of those matters is a separate question from why our own file fails.

## Proposed outcome

I can put two objects on the plate, give them a head each, and get both off the plate
intact — from a file this repo's profile produced, not QIDI's.

Good enough looks like: the two-cube job prints to completion, the walls are solid
rather than spongey, and it finishes somewhere near the time OrcaSlicer predicts
instead of taking five hours.

Stringing and colour alignment are wanted too, but they are not what "done" hangs on
here. The reference file strings as well.

## Affected users and systems

Me, and anyone who installs this profile and owns the second hotend. In the repo: the
machine profile's tool-change block, the process profiles, and whatever the validation
harness has to learn about the new shape. Nothing about single-head printing should
move — tests 1 and 3 already pass and must keep passing.

## Constraints

- [Hard rule 1](../CLAUDE.md#hard-rules-do-not-relax-these) — whatever goes in comes
  from QIDI's own file or the base profile, not from a number that looks about right.
- [Hard rule 4](../CLAUDE.md#hard-rules-do-not-relax-these) — the head lift is the
  firmware's business. The control print says it works. Leave it alone.
- [Hard rule 5](../CLAUDE.md#hard-rules-do-not-relax-these) — extruder offsets stay
  zero in the slicer, including if the colour misalignment turns out to be real.
- Absolute E stays, so the prime tower stays off. That was settled in task 6 and the
  slicer refuses outright otherwise.

## Open questions

Live in [`TODO.md`](../TODO.md) — see *Found by the first dual print*.

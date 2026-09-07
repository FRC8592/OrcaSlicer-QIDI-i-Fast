# TODO

Every value that is not yet traced to the base OrcaSlicer profile, QIDI's published
profiles, or the reference G-code. Nothing ships with an invented default —
see the "derive, don't invent" rule in [`CLAUDE.md`](CLAUDE.md).

## Next steps

Handoff tasks, with current state. Task 1 is partly done (results in `CLAUDE.md`);
nothing else has been started.

- [x] **1. Recon the schema** — machine/process inherits chains, legacy-vs-Klipper
      machine inventory, user config dir, and the base-profile choice are recorded in
      `CLAUDE.md`. Base: **`Qidi X-CF Pro 0.4 nozzle`** (300×250×300 vs the i-Fast's
      330×250×320, closest of the three legacy machines; X-Plus is much smaller).
      Still owed: the *flattened* key list for the X-CF Pro chain, and confirmation of
      exactly which fields Orca requires before it will load a user profile without
      silently rejecting it.
- [ ] **2. Extract ground truth → `reference/extracted-gcode.md`** — verbatim start
      block, end block, chamber commands, heating order, every QIDI-specific M-code
      explained, and the full tool-change sequence from the dual file. Much of this is
      already summarised in `CLAUDE.md`; this task is to write it out *verbatim* with
      commentary. **This is the natural next task.**
- [ ] **3. Machine profile** — from the X-CF Pro base: 330×250×320, two extruders as
      multi-tool (`single_extruder_multi_material: "0"` + `nozzle_diameter: ["0.4","0.4"]`),
      zero extruder offsets, motion limits carried over unchanged, and the step-2 blocks
      as `machine_start_gcode` / `machine_end_gcode` / `change_filament_gcode`.
- [ ] **4. Process profile** — 0.20 mm standard, inheriting from
      `0.20mm Standard @Qidi XCFPro`. Add 0.15/0.30 only if trivial. Do **not** import
      speeds from QIDI's Cura profile.
- [ ] **5. Filament profile** — one generic PLA inheriting Orca's generic PLA, temps
      from QIDI's reference profile, bed 80 °C (see above).
- [ ] **6. Validate** — derive the Orca CLI invocation from `--help` and the repo docs
      (do not assume flag names). Slice a test model, diff against the reference
      ignoring coordinates and comments, report every difference in the start block,
      end block, temperature commands and M-codes. Repeat for the dual case. Requires
      OrcaSlicer 2.4.2 installed — currently only 2.3.1 is.
- [ ] **7. Package** — fill in `README.md` provenance, finish install instructions,
      confirm the AGPL-3.0 / Bambu Studio / PrusaSlicer attribution chain.

## Open questions for the human

- [ ] **Which head assembly is installed** — standard brass, or the 350 °C high-temp
      variant? Sets `nozzle_max_temperature`. Per the handoff we default to standard
      brass; the reference G-code only ever reaches 230 °C, so it cannot distinguish
      them. Needs eyes on the machine.
- [ ] **Are any non-0.4 nozzles on hand?** See "Nozzle sizes" below. Not blocking.

## Decided

- [x] **Target OrcaSlicer version: 2.4.2** (2026-09-07). Base profiles come from the
      `v2.4.2` tag of the clone, not its 2.5.0-dev working tree. Only the 2.3.1
      AppImage is installed, so 2.4.2 must be installed before load-testing.
- [x] **Bed temperature: 80 °C**, from `reference/single-extruder.gcode` (`M140 S80`),
      overriding the 60 °C in `reference/qidi-profiles/prusaslicer/PrusaSlicer_fast.ini`.
      G-code is ground truth. Record the discrepancy in `README.md`.
- [x] **`A`/`B` extruder axes: not an issue.** All 5 occurrences in each reference file
      are inside the start block's prime line; the print body and the tool change use
      plain `E`. Since the start block is pasted verbatim, nothing special is needed.
- [x] **`single_extruder_multi_material: "0"`**, paired with
      `nozzle_diameter: ["0.4","0.4"]` — the flag alone does not change the extruder
      count. Full reasoning in `CLAUDE.md`.
- [x] **Nozzle sizes: 0.4 only for now.** The only size QIDI documents for the i-Fast.

## Nozzle sizes — what adding more would take

Machine-side is trivial: a per-nozzle profile is a ~15-key file that `inherits` the 0.4
machine profile and overrides `name`, `nozzle_diameter`, `printer_variant`, and
`default_print_profile` (pattern: `Qidi X-Max 3 0.6 nozzle.json`).

The cost is the **process** profile each one must point at. QIDI publishes nothing for
the i-Fast beyond 0.4, and Orca ships no legacy-QIDI process profiles for other sizes,
so every layer height, line width and flow value would be invented — exactly what rule 1
forbids. If we add them, each derived value gets a `TODO(verify):` and the README says
plainly that those variants are unproven.

Revisit once 0.4 has produced a good print.

## Deferred until a second material exists

- [ ] **Ooze prevention / idle nozzle temperature.** The dual reference drops the parked
      hotend to 150 °C and ramps it back (`M104 T0 S150` → `S168.3` → `S200`). Orca's
      equivalent is `ooze_prevention` + filament `idle_temperature` (or
      `standby_temperature_delta`), with `preheat_time` for the ramp. Irrelevant to a
      single-PLA profile, needed to match the reference on a two-material job.
- [ ] **`bed_temperature_formula`.** Defaults to `by_highest_temp`. Harmless while every
      i-Fast filament profile says 80 °C; revisit if one ever doesn't.

## Unverified profile values

_Populated as profiles are written._

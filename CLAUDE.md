# CLAUDE.md

Guidance for Claude Code working in this repo.

## What this repo is

An **OrcaSlicer printer profile for the QIDI i-Fast** — machine + process + minimal
filament JSONs, derived from OrcaSlicer's stock QIDI *legacy* profiles and validated
against reference G-code exported from QIDI Print.

This is a **data/config repo, not a code repo.** There is nothing to build or compile.
The deliverable is JSON profiles plus documentation of where every value came from.

The authoritative spec is [`ifast-orca-profile-handoff.md`](ifast-orca-profile-handoff.md).
Read it before doing task work; it defines the objective, the 7 tasks, the hard rules,
and the definition of done. This file records the environment facts and recon results
that the handoff assumes you will discover.

## The machine

QIDI i-Fast (~2021). Enclosed, linear rails, dual Z, **dual extruder**.

- Build volume **330 × 250 × 320 mm**
- Two independent hotends, **multi-tool** (`single_extruder_multi_material = 0`) — not an MMU
- Firmware-managed head auto-lift on tool change. The slicer only emits `T0` / `T1`.
- Extruder offsets are handled in firmware → **must be zero in the slicer** (else double-applied)
- Bed to 100 °C, actively heated chamber to 60 °C (`M141`)
- Chitu-derived board, Marlin-flavored G-code
- Standard brass head assumed; a 350 °C high-temp head exists as an option

**This is the legacy QIDI generation.** Unrelated to X-Max 3 / X-Plus 3 / Q1 / Q2 /
Plus 4 / Plus 5, which are Klipper machines with a completely different motion system.

## Environment (verified 2026-09-07)

| Thing | Location / value |
|---|---|
| OrcaSlicer clone | `/home/brad/Projects/OrcaSlicer/OrcaSlicer` (note: **not** `OracSlicer`) |
| Clone state | branch `main`, `2.5.0-dev`. **Target the `v2.4.2` tag** — read profiles with `git show v2.4.2:<path>` rather than from the working tree |
| Qidi vendor bundle | `<clone>/resources/profiles/Qidi.json` + `<clone>/resources/profiles/Qidi/` (bundle `02.04.00.06` at `v2.4.2`; `02.04.00.12` on `main`) |
| Installed Orca | AppImages `2.0.0`, `2.2.0`, `2.3.1` in `~/Applications`; flatpak `io.github.softfever.OrcaSlicer` 2.0.0 |
| User config dir | `~/.config/OrcaSlicer/user/default/{machine,process,filament}/` (exists, currently empty) |
| Config schema version | `~/.config/OrcaSlicer/OrcaSlicer.conf` reports `01.08.04.51` (= last run by Orca 2.0.0) |

**Target version: OrcaSlicer 2.4.2** (decided 2026-09-07). The working tree is a
2.5.0-dev nightly, so pull base profiles from the tag, not the tree:
`git show v2.4.2:"resources/profiles/Qidi/machine/Qidi X-CF Pro 0.4 nozzle.json"`.

The `v2.4.2 → main` drift in our base chain is one cosmetic rename
(`default_filament_profile`: `"Qidi Generic PLA"` → `"Generic PLA @Qidi"` in both
`Qidi X-CF Pro 0.4 nozzle.json` and `fdm_qidi_common.json`). Nothing else differs, so
working from the tree is *mostly* safe — but the tag is authoritative.

Note the newest **installed** build is the 2.3.1 AppImage. To actually load and test
the profile, 2.4.2 will need installing.

## Recon results (task 1, partially done)

**Legacy QIDI machines present in the clone** (the only valid base candidates):

| Profile | Build volume | SEMM |
|---|---|---|
| `Qidi X-CF Pro 0.4 nozzle` | 300 × 250 × 300 | `"1"` |
| `Qidi X-Max 0.4 nozzle` | 300 × 250 × 300 | — |
| `Qidi X-Plus 0.4 nozzle` | 270 × 200 × 200 | — |

Everything else in `Qidi/machine/` (X-Max 3/4, X-Plus 3/4/5, X-Smart 3, Q1 Pro, Q2, Q2C)
is Klipper-generation. **Never source values from those.**

**Inherits chain** (machine): `Qidi X-CF Pro 0.4 nozzle` → `fdm_qidi_common` →
`fdm_machine_common` (root, `inherits` absent). Also present but unrelated:
`fdm_qidi_x3_common`, `fdm_q_common`, `fdm_machine_x_common` (Klipper side).

### `single_extruder_multi_material` — why it must be flipped to `0`

`Qidi X-CF Pro 0.4 nozzle` ships `single_extruder_multi_material: "1"` (SEMM). That
describes an MMU-style machine: **one** hotend fed several filaments. The i-Fast is the
other kind — **two** independent hotends. The flag is not cosmetic; it changes four
things in the slicer:

1. **How the extruder count is derived** (`Preset::normalize`, `src/libslic3r/Preset.cpp:462`).
   With SEMM on, Orca counts *filaments* from `filament_diameter` and calls
   `set_num_filaments()`. With SEMM off it counts *extruders* from the length of the
   `nozzle_diameter` array and calls `set_num_extruders()`. So the i-Fast needs both
   `single_extruder_multi_material: "0"` **and** `nozzle_diameter: ["0.4","0.4"]`;
   the flag alone does nothing, and the array alone is ignored.
2. **Whether `extruder_offset` is per-tool** (`GCode.cpp:1800`, `1861`). SEMM on always
   applies `extruder_offset[0]`; SEMM off applies the offset of the tool being selected.
   Ours are zero either way — the firmware owns them — but SEMM off is the honest setting.
3. **Whether Orca resets E at a tool change** (`GCode.cpp:9665`, `m_writer.reset_e()`).
   Only under SEMM. With SEMM off, the `G92 E0` the reference shows around `T0`/`T1`
   must come from our `change_filament_gcode`.
4. **Whether Orca emits the tool-change temperature itself** (`GCode.cpp:9681`). Only
   under SEMM, and only without a prime tower. With SEMM off, the reference's
   `M109 S200` likewise has to live in `change_filament_gcode`.

Points 3 and 4 line up with what the reference G-code actually does — QIDI Print puts
`G92 E0`, `M109`, `M106` and the prime in the tool-change block — so SEMM `0` plus a
verbatim `change_filament_gcode` reproduces it. Related: `ooze_prevention` is only
supported with SEMM off (`Print.cpp:1522`) — and we do want it eventually, since the
reference drops the idle nozzle to 150 °C. See "Standby / idle nozzle temperature" below.

**Nozzle sizes.** Ship **0.4 only.** It is the sole nozzle QIDI documents for the
i-Fast (`PrusaSlicer_fast.ini`: `nozzle_diameter = 0.4,0.4`), and process values for
other sizes have no source — inventing them breaks rule 1. Adding sizes later is cheap:
Orca's per-nozzle machine profiles are thin overrides that `inherits` the 0.4 profile
and set only `name`, `nozzle_diameter`, `printer_variant` and `default_print_profile`
(see `Qidi X-Max 3 0.6 nozzle.json`, 15 keys). The cost is the *process* profile each
one points at. See `TODO.md`.

**Process chain**: `0.20mm Standard @Qidi XCFPro` → `fdm_process_qidi_common`.
Legacy layer heights available: 0.12 / 0.16 / 0.20 / 0.25 / 0.30, each in
`@Qidi XCFPro`, `@Qidi XMax`, `@Qidi XPlus` variants, gated by `compatible_printers`.

**Profile file shape** — a user profile needs `type` (`machine`/`process`/`filament`),
`name`, `inherits`, `from`, `instantiation`, and for machines `printer_model` /
`nozzle_diameter` / `printable_area` / `printable_height`. System profiles carry
`setting_id`; user profiles use `"from": "User"` and no vendor `setting_id`.
Confirm exact requirements against the clone's loader before writing files — Orca
silently rejects malformed profiles.

## Ground truth from the reference G-code

`reference/single-extruder.gcode` and `reference/dual-extruder.gcode` are **the
authority on machine behavior**. Use their blocks verbatim. Do not tidy them.

Key facts already established:

- Exported by **`Cura_SteamEngine 4.9.1`** (QIDI Print is Cura-derived), `;FLAVOR:Marlin`
- **`A`/`B` axes appear only in the start block, and only for the prime line.** All
  5 occurrences in each file sit inside the start G-code (`G92 A0 B0`, `G1 X330 B19 F2400`,
  `G1 X5 A19 F2400`); the print body uses plain `E` throughout (1,855 `E` moves in the
  single file, 7,900 in the dual), and so does the tool change. `A` is extruder 0's axis
  and `B` is extruder 1's, which lets QIDI Print prime both hotends without a tool change.
  Since we paste the start block in verbatim, **this needs no special handling** — Orca
  emits `E` for the body, matching the reference.
- M-codes in play: `G0 G1 G28 G92 M82 M84 M104 M106 M107 M109 M140 M141 M190 M2100 M4010`
  - `M4010` — QIDI thumbnail/preview blob (131 lines of it precede the start block)
  - `M2100 T<seconds>` — print time estimate
  - `M141 S<n>` — chamber heater (reference sets `M141 S0`)
- Heating order in the start block: `M140 S80` → `M104 T0 S200` → `M190 S80` → `M109 T0 S200`
- Prime line runs the full X width (`X330`) using both tools
- End block: `M107` / `M140 S0` / `M104 S0 T0` / `M104 S0 T1`, retract `G1 E-1 F300 Z320`,
  park `G0 F3600 X320 Y0`, `M84`
- Tool change (dual): retract → travel to `X330` → `G1 F1200 E8.5` → `G92 E0` → `T<n>` →
  `G92 E0` → `M109 S<temp>` → `M106 S<fan>` → `G1 F1200 E8.5` prime → resume

Write the full verbatim extraction to `reference/extracted-gcode.md` (task 2).

## QIDI's published profiles

`reference/qidi-profiles/` holds QIDI's legacy bundle. The i-Fast files are:

- `prusaslicer/PrusaSlicer_fast.ini` — **most useful**; confirms `bed_shape = 0x0,330x0,330x250,0x250`,
  `max_print_height = 320`, `extruder_offset = 0x0,0x0`, `single_extruder_multi_material = 0`,
  `gcode_flavor = marlin`, `nozzle_diameter = 0.4,0.4`, and the motion limits
- `simplify3D/Qidi Technology i-fast.fff`
- `ideaMaker/i-fast-export.printer`, `i-fast-PLA-export.bin`
- `CURA/qidi.zip`

Note a conflict, **resolved in favour of the G-code**: this ini says bed 60 °C, but the
reference emits `M140 S80`. Use 80 °C and record the discrepancy in `README.md`.

### Bed temperature and the mixed-material reference

The dual file prints **PLA on T0 and PETG on T1** (`M104 T0 S200` / `M104 T1 S230`), so
it is fair to ask whether its bed temperature is a PLA number or a PETG number. It is
neither — it is the same number:

| File | Materials | Bed |
|---|---|---|
| `single-extruder.gcode` | PLA | `M140 S80` / `M190 S80` |
| `dual-extruder.gcode` | PLA + PETG | `M140 S80` / `M190 S80` |

Four bed commands per file, all of them in the start block or the shutdown block. The
bed is **never changed mid-print**, and adding PETG did not move it. So 80 °C is not
"QIDI's PLA bed temp" — it is what QIDI Print asks for on this machine either way, and
it is safe to carry into a PLA-only profile.

That said, **bed temperature is a filament property in Orca**, not a machine or process
one — `hot_plate_temp` and `hot_plate_temp_initial_layer` (`PrintConfig.cpp:1169`, `1223`),
keyed per bed type. It therefore lives in our generic PLA filament profile, not the
machine profile. Two consequences once a second material is added:

- The print-level enum **`bed_temperature_formula`** decides what a mixed job emits:
  `by_highest_temp` (the **default**, `PrintConfig.cpp` / `GCode.cpp:3531`) takes the max
  across the filaments in the job; `by_first_filament` takes the first extruder's
  (`GCode.cpp:3533`). If every i-Fast filament profile we write says 80, both formulas
  agree and the reference is reproduced either way. Keep it that way unless there is a
  reason not to.
- The start G-code must use the **scalar** placeholder `bed_temperature_initial_layer_single`
  (`GCode.cpp:3538`), which is the resolved single value. The X-CF Pro base start G-code
  uses the vector `[hot_plate_temp_initial_layer]`, which is per-filament and is the wrong
  shape for a two-extruder machine emitting one `M140`.

### Standby / idle nozzle temperature — the reference does this

The dual file drops the inactive hotend and ramps it back before use:

```gcode
M104 T0 S150     ; T0 parked -> standby
M104 T0 S168.3   ; interpolated preheat back up
M104 T0 S200     ; back to print temp
```

Orca's equivalent is **`ooze_prevention`** (print setting, "drop the temperature of the
inactive extruders"), with the target from the filament's `idle_temperature`, or from
`standby_temperature_delta` when `idle_temperature` is 0. The ramp is `preheat_time`.

**This corrects an earlier note in this file's history:** ooze prevention should be
*enabled*, not disabled, if we want to match the reference. It is not a substitute for
the firmware auto-lift — that is separate and stays untouched — it is the temperature
half of the same idea. Conveniently it is only supported with SEMM **off**
(`Print.cpp:1522`), which is what we are already doing.

Deferred, though: the handoff scopes the first profile to one PLA filament, where an
idle extruder never happens. Enable and tune it when the second material lands.

Other `.ini` files here (`_max`, `_plus`, `_pro`, `_cf_pro`, `_maker`, `_mates`) are
sibling machines — useful for cross-checking, not for sourcing i-Fast values.

## Hard rules (from the handoff — do not relax these)

1. **Derive, don't invent.** Every value traces to the base Orca profile, QIDI's published
   profiles, or the reference G-code. No source → emit `TODO(verify): <what, and why it
   matters>` instead of a plausible default from another printer.
2. **Never source from Klipper-generation QIDI machines.**
3. **No network / print-host configuration.** The i-Fast speaks a proprietary UDP protocol
   Orca does not support. G-code moves by USB stick.
4. **Don't touch the auto-lift mechanism.** Firmware behavior; slicer only emits `T0`/`T1`.
5. **Extruder offsets stay zero.**
6. **Don't raise motion limits.** Carry them from the base profile. Not a fast machine.
7. **Report every diff during validation.** Never suppress a diff to make a check pass.
8. **Ask before guessing about the physical machine.** The user has it in front of them.

## Repo layout

```
profiles/{machine,process,filament}/   # the deliverable JSONs, mapping onto Orca's user config dirs
reference/                             # inputs: QIDI Print G-code + QIDI's published profiles
  single-extruder.gcode                #   ground truth: start/end blocks, M-codes
  dual-extruder.gcode                  #   ground truth: tool-change sequence
  qidi-profiles/                       #   QIDI's legacy bundle (PrusaSlicer/Cura/S3D/ideaMaker)
scripts/                               # validation harness (task 6)
ifast-orca-profile-handoff.md          # the spec
README.md                              # provenance: which value came from where
TODO.md                                # every unverified value
```

`.gitignore` excludes `/.idea/`, `*.iml` (JetBrains-opened project), and `/out/` for
validation output. `.gitattributes` protects the byte-exactness of `reference/**`.

## Conventions

- Profile JSONs use **tab indentation** and match Orca's stock key ordering, so diffs
  against the clone's files stay readable.
- Reference G-code and QIDI's published profiles are **read-only inputs**. Never edit them.
  `.gitattributes` marks `reference/**` as `-text -diff` so Git cannot rewrite CRLF line
  endings there — the committed blobs are byte-identical to what QIDI Print produced.
  (Verified: `sha1sum` of worktree and index match for both G-code files.) Do not relax
  this; `core.autocrlf=input` is set on this machine and would otherwise normalise them.
- Every value added to a profile gets a line in `README.md` naming its source, or a
  `TODO(verify):` entry in `TODO.md`. A profile that fails loudly beats one that slices
  fine and prints badly.
- OrcaSlicer profiles are AGPL-3.0 and derive from Bambu Studio and PrusaSlicer upstream.
  Preserve that attribution chain in `README.md`.

## Validation (task 6)

Determine the Orca CLI invocation from `--help` and the clone's docs — **do not assume
flag names**, they have changed across versions. The check must slice a test model,
then diff the output against the reference G-code ignoring coordinates and comments,
reporting differences in the start block, end block, temperature commands, and M-codes.
Repeat for a two-material model against `dual-extruder.gcode`.

## Definition of done

- Orca loads the profile with no warnings; i-Fast appears with the correct build volume
- Single-extruder slice: start block, end block, and M-codes match the QIDI Print reference
- Dual-extruder slice: tool-change sequence matches the reference
- `TODO.md` lists every unverified value
- `README.md` explains where each setting came from

Explicitly **out of scope** until after a first successful print: tuned retraction, flow
calibration, pressure advance, per-material profiles, chamber-temperature workflows.

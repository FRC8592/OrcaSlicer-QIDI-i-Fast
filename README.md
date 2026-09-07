# QIDI i-Fast — OrcaSlicer profile

> **Status: machine profile written and load-tested against OrcaSlicer 2.4.2.** A real
> single-extruder slice emits an end block byte-identical to the QIDI Print reference and
> a start block identical apart from one commented-out line. The process and filament
> profiles (tasks 4–5) and the validation harness (task 6) are still to come; the
> tool-change block is derived from source but not yet executed. See
> [`TODO.md`](TODO.md) for every unverified value and
> [`ifast-orca-profile-handoff.md`](ifast-orca-profile-handoff.md) for the spec.

An OrcaSlicer printer profile (machine + process + minimal filament) for the
**QIDI i-Fast**, a machine OrcaSlicer does not ship a profile for.

- Build volume 330 × 250 × 320 mm, dual extruder (multi-tool), heated chamber
- Legacy QIDI generation — Chitu board, Marlin-flavored G-code, **not** Klipper
- Targets **OrcaSlicer 2.4.2**

## Installation (Linux)

Profiles are plain JSON dropped into OrcaSlicer's user config directory. **Which
directory depends on how OrcaSlicer was installed:**

| Install | User profile directory |
|---|---|
| Flatpak `com.orcaslicer.OrcaSlicer` | `~/.var/app/com.orcaslicer.OrcaSlicer/config/OrcaSlicer/user/default/` |
| AppImage / native | `~/.config/OrcaSlicer/user/default/` |

```bash
ORCA=~/.var/app/com.orcaslicer.OrcaSlicer/config/OrcaSlicer/user/default   # flatpak
cp "profiles/machine/QIDI i-Fast 0.4 nozzle.json" "$ORCA/machine/"
```

**Before the profile will load**, the QIDI vendor must be installed in OrcaSlicer, because
the profile `inherits` a QIDI system preset. Run OrcaSlicer's configuration wizard once and
enable **QIDI → X-Max (0.4 nozzle)**. Without it the profile is dropped at startup with
`can not find parent Qidi X-Max 0.4 nozzle for config …` in the log and no visible error.

Two operational warnings:

- **Copy, never edit in place.** If a preset throws while loading, OrcaSlicer *deletes the
  file* (`v2.4.2:Preset.cpp:1641`–`1651`). This repo is the source of truth.
- **A missing or unparseable `version` key is a silent no-op** — the preset is skipped with
  no log line at all (`Preset.cpp:1653`–`1656`).

## Provenance

### Derived from

`Qidi X-Max 0.4 nozzle` (OrcaSlicer `v2.4.2`, Qidi vendor bundle `02.04.00.06`), whose
chain is `Qidi X-Max 0.4 nozzle` → `fdm_qidi_common` → `fdm_machine_common`.

Chosen over `Qidi X-CF Pro 0.4 nozzle` — the two are byte-identical at `v2.4.2` apart from
`name`, `setting_id`, `printer_model`, `default_print_profile`, `machine_start_gcode` and
`single_extruder_multi_material`, and X-Max already ships `single_extruder_multi_material:
"0"` (the i-Fast is two independent hotends, not an MMU) plus a legacy-QIDI start block.
The X-CF Pro ships SEMM `"1"`. Both are 300 × 250 × 300, so neither is closer on volume.

Everything not listed below is inherited from that chain unchanged — in particular **all
15 `machine_max_*` motion limits are byte-identical to the base** (hard rule 6).

### Values from QIDI's published profiles

All from `reference/qidi-profiles/prusaslicer/PrusaSlicer_fast.ini`, QIDI's own i-Fast
PrusaSlicer profile:

| Profile key | Value | ini source |
|---|---|---|
| `printable_area` | `0x0, 330x0, 330x250, 0x250` | `bed_shape` |
| `printable_height` | `320` | `max_print_height` |
| `nozzle_diameter` | `["0.4","0.4"]` | `nozzle_diameter = 0.4,0.4` |
| `extruder_offset` | `["0x0","0x0"]` | `extruder_offset = 0x0,0x0` |
| `single_extruder_multi_material` | `"0"` | `single_extruder_multi_material = 0` |
| `gcode_flavor` | `marlin` | `gcode_flavor = marlin` |
| `use_relative_e_distances` | `"0"` | `use_relative_e_distances = 0` |
| `disable_m73` | `"1"` | `remaining_times = 0` (and zero `M73` in either reference) |

The ini also **cross-confirms the base profile's motion limits**: every `machine_max_*`
matches the base exactly, with one exception — `machine_max_acceleration_e` is `10000,5000`
in the ini against the base's `5000,5000`. Hard rule 6 says do not raise motion limits, so
the base value ships. Recorded in `TODO.md`.

### Values from the reference G-code

`reference/single-extruder.gcode` and `reference/dual-extruder.gcode`, extracted verbatim
in [`reference/extracted-gcode.md`](reference/extracted-gcode.md):

| Profile key | Source | Fidelity |
|---|---|---|
| `machine_start_gcode` | §2 start block | Expands **byte-for-byte** to both reference files |
| `machine_end_gcode` | §4 end block, all 15 lines | **Byte-identical** |
| `change_filament_gcode` | §7 variant C | Structure reproduced; see the accepted diffs in `TODO.md` |
| `use_relative_e_distances: "0"` | `M82` + absolute `E` on every move | Necessary: the option **defaults to `true`** and the base chain never sets it |

The start block is templated in exactly four places, so one string reproduces both the
single- and dual-extruder exports:

- `M140` / `M190` → `[bed_temperature_initial_layer_single]` (the resolved *scalar*; the
  base's `[bed_temperature_initial_layer]` is a per-filament vector and the wrong shape
  for a two-extruder machine emitting one `M140`)
- nozzle temperatures → `{nozzle_temperature_initial_layer[0|1]}`
- the `T1` heating pair → `{if is_extruder_used[1]}…{else};…{endif}`, reproducing QIDI
  Print's habit of *commenting the lines out* when T1 is unused
- the prime line's extrusion → `B{is_extruder_used[1] ? 19 : 0}`

**Bed temperature is 80 °C**, from `M140 S80` / `M190 S80` in both references. This
contradicts `PrusaSlicer_fast.ini`, which says 60 °C; the G-code is ground truth. The value
itself is a *filament* property in Orca (`hot_plate_temp`), so it lands in the filament
profile (task 5), not here. Both references emit the same 80 °C with PLA alone and with
PLA + PETG, so it is not a material-specific number.

### Values forced by OrcaSlicer's own behaviour

- **`disable_m73: "1"`** — without it Orca injects `M73 P<n> R<n>` progress lines *into*
  the custom start and end blocks. Both references contain zero `M73`, and QIDI's ini
  sets `remaining_times = 0`.
- **`default_bed_type: "3"`** — the numeric `btPEI` ("High Temp Plate"). It must be
  numeric: `Preset::get_default_bed_type` (`v2.4.2:Preset.cpp:966`–`980`) parses it with
  `atoi`, not the bed-type name map, so `"High Temp Plate"` logs an error on every load.
  It falls back to `btPEI` regardless, so this is explicitness rather than a change.
  **Caveat:** `default_bed_type` is read only by the GUI; the CLI's `curr_bed_type`
  defaults to Cool Plate. The filament profile therefore has to set *every* plate-temp
  variant to 80 °C or GUI and CLI slices will disagree — see `TODO.md`.

### Deliberately not configured

- **Network / print-host.** The i-Fast speaks a proprietary UDP protocol OrcaSlicer does
  not support; G-code reaches it by USB stick.
- **Extruder offsets** stay zero — the firmware applies them, and setting them here would
  double-apply.
- **Head auto-lift on tool change** is firmware behaviour. The slicer only emits `T0`/`T1`.
- **Chamber heater.** Both references emit only `M141 S0` and no `M191`. The machine has an
  actively heated chamber; QIDI Print simply does not drive it.

### Unverified values

See [`TODO.md`](TODO.md).

## Scope

Explicitly out of scope until after a first successful print: tuned retraction, flow
calibration, pressure advance, per-material profiles, chamber-temperature workflows.

## Attribution and license

The profiles here derive from OrcaSlicer's stock QIDI vendor profiles, which are
licensed **AGPL-3.0** and themselves derive from **Bambu Studio** and **PrusaSlicer**
upstream. That attribution chain is preserved: this repo is AGPL-3.0.

## First print

Single extruder, PLA, small model, supervised, chamber heater off. Get that clean
before trusting anything else in here.

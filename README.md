# QIDI i-Fast — OrcaSlicer profile

> **Status: machine and process profiles written and slice-tested against OrcaSlicer
> 2.4.2.** A real single-extruder slice emits an end block byte-identical to the QIDI
> Print reference and a start block identical apart from six temperature values, which
> come from the stock filament preset and land in task 5. The filament profile (task 5)
> and the validation harness (task 6) are still to come; the tool-change block is derived
> from source but not yet executed. See
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
cp profiles/process/*.json "$ORCA/process/"
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

Two inherited G-code keys are **cleared**, both because the reference has no trace of
them and `fdm_machine_common` supplies them by default:

- **`before_layer_change_gcode: ""`** — the base ships `";BEFORE_LAYER_CHANGE\n;[layer_z]\nG92 E0\n"`,
  which combined with our absolute-E setting makes OrcaSlicer refuse to slice outright
  (`"G92 E0" was found in before_layer_change_gcode, which is incompatible with absolute
  extruder addressing`, exit `-51`). The reference has no per-layer `G92 E0` at all: every
  `G92` in `single-extruder.gcode` is in the start block or the end block.
- **`time_lapse_gcode: ""`** — the base ships `";TIMELAPSE_TAKE_FRAME\n"`, which OrcaSlicer
  emits once per layer even with `timelapse_type = 0`. Neither reference contains it.

Both were invisible until the process profiles were slice-tested through a flattened
chain, because the CLI never resolved `inherits` and so never saw the inherited values.
The GUI does resolve it, so both would have bitten on first use.

**Bed temperature is 80 °C**, from `M140 S80` / `M190 S80` in both references. This
contradicts `PrusaSlicer_fast.ini`, which says 60 °C; the G-code is ground truth. The value
itself is a *filament* property in Orca (`hot_plate_temp`), so it lands in the filament
profile (task 5), not here. Both references emit the same 80 °C with PLA alone and with
PLA + PETG, so it is not a material-specific number.

## Process profiles

Five presets, one per layer height OrcaSlicer `v2.4.2` ships for the legacy X-Max:

| Preset | Inherits |
|---|---|
| `0.12mm Fine @QIDI i-Fast` | `0.12mm Fine @Qidi XMax` |
| `0.16mm Optimal @QIDI i-Fast` | `0.16mm Optimal @Qidi XMax` |
| `0.20mm Standard @QIDI i-Fast` | `0.20mm Standard @Qidi XMax` |
| `0.25mm Draft @QIDI i-Fast` | `0.25mm Draft @Qidi XMax` |
| `0.30mm Extra Draft @QIDI i-Fast` | `0.30mm Extra Draft @Qidi XMax` |

Each is a thin override that changes **three values**. Everything else — every speed,
acceleration, line width, shell count and infill setting — is inherited from
`<name> @Qidi XMax` → `fdm_process_qidi_common` → `fdm_process_common` unchanged. Per the
handoff, nothing is converted from QIDI's Cura profile. The inherited line widths are
independently corroborated by `PrusaSlicer_fast.ini`: `initial_layer_line_width` 0.42 =
`first_layer_extrusion_width`, `inner_wall_line_width` 0.45 = `perimeter_extrusion_width`,
`sparse_infill_line_width` 0.45 = `infill_extrusion_width`, `top_surface_line_width` 0.4 =
`top_infill_extrusion_width`.

| Key | Value | Source |
|---|---|---|
| `initial_layer_print_height` | `0.3` | Reference G-code: layer 0 at `Z0.3`, later layers `Z0.5 / Z0.7 / Z0.9` |
| `enable_prime_tower` | `0` | `wipe_tower = 0` in `PrusaSlicer_fast.ini`, and no tower in the dual reference |
| `compatible_printers` | both printer names | Required by two different OrcaSlicer code paths |

**First layer 0.3 mm, on all five.** The stock profiles each set this equal to their own
layer height, and QIDI's ini says 0.35 — the reference G-code wins, and it applies to
every variant because the start block's hardcoded `G0 X0 Y4 Z0.3` prime line assumes it.
Recorded in `TODO.md` as needing a first-print check.

**No prime tower**, from two independent sources plus a mechanical requirement. QIDI's own
PrusaSlicer profile sets `wipe_tower = 0`, and `dual-extruder.gcode` has no tower in the
print body — the only sub-`X20` coordinates in the whole file are the `X0`/`X5` of the
start block. It is also load-bearing: with a prime tower OrcaSlicer takes the
`WipeTowerIntegration` path (`v2.4.2:GCode.cpp:813`+) instead of `GCode::set_extruder`
(`:7952`), and the `change_filament_gcode` above never runs. The stock bases all set `"1"`,
so this cannot be left to inheritance.

**Both printer names in `compatible_printers`**, because the GUI and the CLI check
different things. `is_compatible_with_printer` (`v2.4.2:Preset.cpp:837`–`839`) matches the
active printer's *preset name*, `"QIDI i-Fast 0.4 nozzle"`; the CLI (`OrcaSlicer.cpp:2578`)
matches `new_printer_system_name`, which is the machine preset's ***`inherits`*** value
(`:2045`), `"Qidi X-Max 0.4 nozzle"`. Listing only ours fails a CLI slice with
`-17 CLI_PROCESS_NOT_COMPATIBLE`. `compatible_printers_condition` is not an alternative —
the CLI never evaluates it. The side effect is that these presets also show up under the
stock `Qidi X-Max 0.4 nozzle` printer in the GUI.

### Slicing from the CLI needs a flattened preset

OrcaSlicer's CLI reads each `--load-settings` file **raw and does not resolve `inherits`**
(the handling is commented out in `load_config_file`, `v2.4.2:src/OrcaSlicer.cpp:1953`–`2020`);
missing keys fall back to OrcaSlicer's built-in FFF defaults at `:3629`. A thin preset is
therefore correct in the GUI but loses every inherited QIDI value from the CLI, silently.
Passing the base as a second process file does not help — a duplicate process config is an
error (`:2074`). The task-6 harness flattens the chain itself, keeping the `inherits` key
in its output because the CLI derives `new_printer_system_name` from it.

This only affects command-line slicing. **Nothing about normal GUI use requires it.**

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

### One expected error in the log

Every slice logs `Invalid T command (T1).` once, at error level. It is benign: the start
block emits `T1` unconditionally because the reference does, but OrcaSlicer's *G-code
post-processor* rejects a tool index beyond the number of filaments **used** in the print
(`v2.4.2:GCode/GCodeProcessor.cpp:5490`). The `T1` is still written to the file correctly;
only the time and filament estimates ignore the prime excursion. Silencing it would mean
deviating from the reference, so it stays. See `TODO.md`.

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

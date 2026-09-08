# QIDI i-Fast — OrcaSlicer profile

> **Status: machine, process and filament profiles written, and validated by a
> repeatable harness against the QIDI Print reference exports.** A single-extruder slice
> emits an end block **byte-identical** to the reference and a start block identical
> apart from two *commented-out* `T1` temperature lines, whose value tracks whatever
> filament sits in extruder 2. A two-material slice emits the tool-change block as
> designed. Run `bash scripts/validate.sh` to reproduce — see
> [Validation](#validation). **Nothing has been printed yet.**
>
> Installing is a copy of seven JSON files — see [Installation](#installation-linux).
> [`TODO.md`](TODO.md) lists every unverified value and every open question;
> [`ifast-orca-profile-handoff.md`](ifast-orca-profile-handoff.md) is the spec.

An OrcaSlicer printer profile (machine + process + minimal filament) for the
**QIDI i-Fast**, a machine OrcaSlicer does not ship a profile for.

- Build volume 330 × 250 × 320 mm, dual extruder (multi-tool), heated chamber
- Legacy QIDI generation — Chitu board, Marlin-flavored G-code, **not** Klipper
- Targets **OrcaSlicer 2.4.2**

## Installation (Linux)

The seven JSON files under `profiles/` map one-to-one onto OrcaSlicer's user config
directories. Installing is a copy — there is nothing to build and nothing to edit.

### 1. Prerequisites

- **OrcaSlicer 2.4.2.** Every preset here carries `version: "02.04.00.06"`, the QIDI
  vendor bundle version that ships with it. Nothing compares that against the
  application version, so the presets will load on a newer OrcaSlicer — but nothing
  here has been validated on one.
- **The QIDI vendor must be installed in OrcaSlicer**, because every preset here
  `inherits` a QIDI system preset. Run the configuration wizard once and enable
  **QIDI**. Any QIDI model works: enabling a vendor copies the *whole* `Qidi.json`
  bundle into `<config>/system/` (`v2.4.2:PresetUpdater.cpp:1068`–`1108`), and the
  per-model tick only controls which presets are *visible*. **QIDI → X-Max
  (0.4 nozzle)** is the natural choice, being the preset this profile derives from.
  Without the vendor the profile is dropped at startup with
  `can not find parent Qidi X-Max 0.4 nozzle for config …` in the log, and **no visible
  error in the GUI**.

### 2. Copy the files

Which directory depends on how OrcaSlicer was installed:

| Install | User profile directory |
|---|---|
| Flatpak `com.orcaslicer.OrcaSlicer` | `~/.var/app/com.orcaslicer.OrcaSlicer/config/OrcaSlicer/user/default/` |
| AppImage / native | `~/.config/OrcaSlicer/user/default/` |

With OrcaSlicer closed:

```bash
ORCA=~/.var/app/com.orcaslicer.OrcaSlicer/config/OrcaSlicer/user/default   # flatpak
mkdir -p "$ORCA"/{machine,process,filament}
cp "profiles/machine/QIDI i-Fast 0.4 nozzle.json" "$ORCA/machine/"
cp profiles/process/*.json  "$ORCA/process/"
cp profiles/filament/*.json "$ORCA/filament/"
```

The filename **is** the preset name on this load path — the `name` key is parsed and
then never read (`v2.4.2:Preset.cpp:1613`–`1615`) — so do not rename the files.

### 3. Confirm it loaded

Start OrcaSlicer and select, in order:

1. **Printer → `QIDI i-Fast 0.4 nozzle`.** It appears as a *user* preset among the QIDI
   printers rather than under a vendor heading of its own: `get_custom_vendor_models`
   skips any preset whose base is another preset
   (`v2.4.2:PresetBundle.cpp:2393`–`2400`), and ours derives from
   `Qidi X-Max 0.4 nozzle`.
2. **Process → `0.20mm Standard @QIDI i-Fast`** — the one layer height with reference
   G-code behind it. See [Process profiles](#process-profiles).
3. **Filament → `QIDI Generic PLA @QIDI i-Fast`.**

Then check the plate reads **330 × 250 × 320 mm**, and slice something small. Exactly
one line at `error` level is expected — `Invalid T command (T1).`, which is benign and
explained under [One expected error in the log](#one-expected-error-in-the-log).
Anything else is not expected.

If a preset does not appear at all, the log is the only place that says why:
`~/.var/app/com.orcaslicer.OrcaSlicer/config/OrcaSlicer/log/` for the flatpak,
`~/.config/OrcaSlicer/log/` for an AppImage.

This procedure is the one that produced the copy installed on the development machine;
all seven installed files are byte-identical to `profiles/` (verified 2026-09-07).

### Two operational warnings

- **Copy, never edit in place.** If a preset throws while loading, OrcaSlicer *deletes
  the file* (`v2.4.2:Preset.cpp:1641`–`1651`). This repo is the source of truth; the
  installed copies are disposable.
- **A missing or unparseable `version` key is a silent no-op** — the preset is skipped
  with no log line at all (`Preset.cpp:1653`–`1656`). If a hand-edited preset vanishes
  from the GUI, check `version` first.

### Updating and uninstalling

Updating is the same copy again, with OrcaSlicer closed. Uninstalling is deleting the
seven files:

```bash
rm "$ORCA/machine/QIDI i-Fast 0.4 nozzle.json"
rm "$ORCA"/process/*"@QIDI i-Fast.json"
rm "$ORCA"/filament/*"@QIDI i-Fast.json"
```

Saving a modified preset in the GUI writes another file into these directories, so list
them before assuming they are clean.

## Provenance

### Derived from

`Qidi X-Max 0.4 nozzle` (OrcaSlicer `v2.4.2`, Qidi vendor bundle `02.04.00.06`), whose
chain is `Qidi X-Max 0.4 nozzle` → `fdm_qidi_common` → `fdm_machine_common`.

Chosen over `Qidi X-CF Pro 0.4 nozzle` — the two are byte-identical at `v2.4.2` apart from
`name`, `setting_id`, `printer_model`, `default_print_profile`, `machine_start_gcode` and
`single_extruder_multi_material`, and X-Max already ships `single_extruder_multi_material:
"0"` (the i-Fast is two independent hotends, not an MMU) plus a legacy-QIDI start block.
The X-CF Pro ships SEMM `"1"`. Both are 300 × 250 × 300, so neither is closer on volume.

### Every key in the machine profile

`profiles/machine/QIDI i-Fast 0.4 nozzle.json` in full. **Anything not in this table is
not in the file** — it is inherited from the chain above unchanged, and that includes
every speed, acceleration and retraction behaviour not listed here.

Four abbreviations for the source column:

- **base** — `Qidi X-Max 0.4 nozzle` → `fdm_qidi_common` → `fdm_machine_common`, `v2.4.2`
- **ini** — `reference/qidi-profiles/prusaslicer/PrusaSlicer_fast.ini`, QIDI's own
  published i-Fast PrusaSlicer profile
- **G-code** — `reference/single-extruder.gcode` / `reference/dual-extruder.gcode`,
  extracted verbatim in [`reference/extracted-gcode.md`](reference/extracted-gcode.md)
- **Orca** — forced by OrcaSlicer's own behaviour, argued in the section named

#### Preset metadata

| Key | Value | Source |
|---|---|---|
| `type` | `machine` | Orca preset shape (`Preset::save`, `v2.4.2:Preset.cpp:675`–`686`) |
| `name` | `QIDI i-Fast 0.4 nozzle` | Must equal the filename and not collide with a system preset (`Preset.cpp:1613`–`1621`) |
| `inherits` | `Qidi X-Max 0.4 nozzle` | base — see [Derived from](#derived-from) |
| `from` | `User` | Orca preset shape; also **mandatory for the CLI** |
| `instantiation` | `true` | Orca preset shape; required of anything another preset inherits |
| `version` | `02.04.00.06` | The QIDI vendor bundle's own version. Mandatory, and must parse as a Semver, or the preset is skipped **silently** |
| `printer_model` | `QIDI i-Fast` | A new model name, deliberately not a QIDI bundle one: reusing `Qidi X-Max` would make `get_current_vendor_type()` classify the i-Fast as `VendorType::Klipper_Qidi` (`PresetBundle.cpp:612`–`641`) |
| `printer_variant` | `0.4` | base — the only nozzle QIDI documents for this machine |
| `default_print_profile` | `0.20mm Standard @QIDI i-Fast` | Our process preset; the one layer height with reference G-code behind it |
| `default_filament_profile` | `["QIDI Generic PLA @QIDI i-Fast"]` | Our filament preset |
| `printer_notes` | provenance note | Ours. A short version of this README, visible in the GUI |

#### Geometry and extruder configuration

| Key | Value | Source |
|---|---|---|
| `printable_area` | `0x0, 330x0, 330x250, 0x250` | ini `bed_shape` |
| `printable_height` | `320` | ini `max_print_height` |
| `nozzle_diameter` | `["0.4","0.4"]` | ini `nozzle_diameter = 0.4,0.4`. The **array length** is what gives Orca two extruders — see below |
| `single_extruder_multi_material` | `"0"` | ini; also the base's value. Two independent hotends, not an MMU |
| `extruder_offset` | `["0x0","0x0"]` | ini `extruder_offset = 0x0,0x0`. The firmware owns the real offsets; a non-zero value here double-applies |
| `gcode_flavor` | `marlin` | ini `gcode_flavor = marlin` (= base) |
| `use_relative_e_distances` | `"0"` | ini `use_relative_e_distances = 0`, and `M82` + an absolute `E` on all 1855 extrusion moves of the single reference. **Necessary, not cosmetic:** the option defaults to `true` and the whole base chain leaves it unset |
| `nozzle_type` | `["brass","brass"]` | The handoff's "assume the standard brass head" — an instruction, not a measurement. The base says `hardened_steel`. Affects only Orca's abrasion warnings. `TODO(verify)` |

`single_extruder_multi_material` and `nozzle_diameter` have to agree: with SEMM off,
`Preset::normalize` counts *extruders* from the length of the `nozzle_diameter` array
(`v2.4.2:Preset.cpp:455`–`462`). The flag alone changes nothing, and the array alone is
ignored.

#### Motion limits — carried from the base, unchanged

All 15 `machine_max_*` keys (`machine_max_acceleration_e`, `…_extruding`,
`…_retracting`, `…_travel`, `…_x/y/z`, `machine_max_speed_e/x/y/z`,
`machine_max_jerk_e/x/y/z`) are **byte-identical to the base** (hard rule 6: this is not
a fast machine, do not raise them). `auxiliary_fan` `"0"` is likewise the base's value,
restated.

The ini independently **cross-confirms** every one of them, with a single exception:
`machine_max_acceleration_e` is `10000,5000` in the ini against the base's `5000,5000`.
Hard rule 6 keeps the base value. Recorded in `TODO.md`.

#### Per-extruder arrays, written out at length 2

| Keys | Value |
|---|---|
| `max_layer_height`, `min_layer_height` | base values, duplicated |
| `retraction_minimum_travel`, `retraction_length`, `retract_length_toolchange`, `retraction_speed`, `deretraction_speed`, `retract_before_wipe`, `retract_when_changing_layer`, `retract_restart_extra`, `retract_restart_extra_toolchange` | base values, duplicated |
| `z_hop`, `z_hop_types`, `wipe`, `wipe_distance`, `extruder_colour` | base values, duplicated |

**No value here differs from the base** — the base simply states each one once, for its
single extruder, and the i-Fast has two. In the GUI Orca would extend them itself:
`Preset::normalize` → `set_num_extruders` (`PrintConfig.cpp:8829`) resizes every
per-extruder vector, duplicating `values.front()` (`Config.hpp:661`). The CLI does not
call `normalize`, so writing them out is what makes a command-line slice see two
extruders configured the same way the GUI would. Retraction tuning is out of scope until
after a first print; `z_hop` `0.4` with `z_hop_types` `Auto Lift` has no counterpart in
the reference and is recorded in `TODO.md`.

#### G-code blocks — from the reference exports

| Key | Source | Fidelity |
|---|---|---|
| `machine_start_gcode` | §2 start block | Expands **byte-for-byte** to both reference files |
| `machine_end_gcode` | §4 end block, all 15 lines | **Byte-identical** |
| `change_filament_gcode` | §7 variant C | Structure reproduced; see the accepted diffs in `TODO.md` |
| `before_layer_change_gcode` | cleared to `""` | The reference has no per-layer `G92 E0` |
| `time_lapse_gcode` | cleared to `""` | Neither reference contains `;TIMELAPSE_TAKE_FRAME` |

#### Forced by OrcaSlicer's own behaviour

| Key | Value | Why |
|---|---|---|
| `disable_m73` | `"1"` | Otherwise Orca injects `M73 P<n> R<n>` progress lines *into* the custom start and end blocks. Zero `M73` in either reference; ini `remaining_times = 0` |
| `default_bed_type` | `"3"` | The **numeric** `btPEI`, "High Temp Plate" |
| `support_air_filtration` | `"0"` | Otherwise `M106 P3 S255` lands after the start block and `M106 P3 S0` after `;End of Gcode` |
| `manual_filament_change` | `"0"` | Orca's own default, restated. With it on, `change_filament_gcode` is skipped at the *first* tool change and every `T` becomes a comment for the whole print (`GCode.cpp:7959`–`7960`, `GCodeWriter.cpp:547`–`551`) — the opposite of what this machine needs |

Each is argued in full under
[Values forced by OrcaSlicer's own behaviour](#values-forced-by-orcaslicers-own-behaviour).

### Notes on the G-code blocks

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
itself is a *filament* property in Orca (`hot_plate_temp`), so it lives in the filament
profile, not here — see [Filament profile](#filament-profile). Both references emit the
same 80 °C with PLA alone and with PLA + PETG, so it is not a material-specific number.

## Process profiles

Five presets, one per layer height OrcaSlicer `v2.4.2` ships for the legacy X-Max:

| Preset | Inherits |
|---|---|
| `0.12mm Fine @QIDI i-Fast` | `0.12mm Fine @Qidi XMax` |
| `0.16mm Optimal @QIDI i-Fast` | `0.16mm Optimal @Qidi XMax` |
| `0.20mm Standard @QIDI i-Fast` | `0.20mm Standard @Qidi XMax` |
| `0.25mm Draft @QIDI i-Fast` | `0.25mm Draft @Qidi XMax` |
| `0.30mm Extra Draft @QIDI i-Fast` | `0.30mm Extra Draft @Qidi XMax` |

Metadata is the same shape as the machine profile's — `type` `process`, `name` matching
the filename, `inherits`, `from` `User`, `instantiation` `true`, `version` `02.04.00.06`.

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

## Filament profile

One preset: **`QIDI Generic PLA @QIDI i-Fast`**, inheriting
`Qidi Generic PLA` → `fdm_filament_pla` → `fdm_filament_common` from the `v2.4.2` Qidi
bundle. Deliberately minimal, per the handoff — flow ratio, retraction and per-material
tuning belong after a first successful print, not here.

| Key | Value | Source |
|---|---|---|
| `nozzle_temperature_initial_layer` | `200` | `M104 T0 S200` / `M109 T0 S200` in both references; `first_layer_temperature = 200` in `PrusaSlicer_fast.ini` |
| `nozzle_temperature` | `200` | `temperature = 200` in `PrusaSlicer_fast.ini`; the single reference never leaves 200 °C (its one mid-print `M104 S200` re-asserts the same value) |
| every `*_plate_temp` and `*_plate_temp_initial_layer` | `80` | `M140 S80` / `M190 S80` in both references |
| `enable_pressure_advance` | `0` | No `M900` in either reference, in `PrusaSlicer_fast.ini`, or in the Simplify3D `.fff` |
| `compatible_printers` | both printer names | Same two code paths as the process profiles |

Plus the same metadata shape, with one filament-only addition: **`filament_id` `GFL99`**,
carried unchanged from the parent `Qidi Generic PLA`. It is the vendor's own id for
generic PLA, and the CLI reads it straight out of the preset (`v2.4.2:OrcaSlicer.cpp:1993`–`1995`),
so it must survive flattening.

Everything else is inherited, including `filament_diameter` `1.75` (which matches
`filament_diameter = 1.75,1.75` in the ini) and `filament_type` `PLA`.

**All twelve plate-temperature keys are set, not just `hot_plate_temp`.** The machine
profile declares `default_bed_type: "3"` (High Temp Plate), but that key is read *only by
the GUI* (`v2.4.2:Plater.cpp:2524`–`2538`); the CLI's `curr_bed_type` falls back to Cool
Plate (`PrintConfig.cpp:1080`+). Setting only `hot_plate_temp*` therefore slices at
`M140 S45` from the CLI and 80 °C from the GUI. The i-Fast has one physical bed, so every
variant — `cool_plate_temp`, `textured_cool_plate_temp`, `eng_plate_temp`,
`hot_plate_temp`, `textured_plate_temp`, `supertack_plate_temp` and each
`*_initial_layer` — is 80. Confirmed empirically: the slice emits `M140 S80` / `M190 S80`.

**Pressure advance is off.** The parent `Qidi Generic PLA` ships
`enable_pressure_advance: 1` with `pressure_advance: 0.031`, which on a `marlin` flavor
makes OrcaSlicer emit `M900 K0.031` (`v2.4.2:GCodeWriter.cpp:388`–`389`). Neither
reference export contains an `M900`, and neither does any of QIDI's published i-Fast
profiles — the 0.031 is an Orca vendor value with no i-Fast provenance, and the handoff
puts pressure advance out of scope until after a first print. `pressure_advance` itself is
left inherited so the number survives for later tuning; it is simply unused. Recorded in
`TODO.md`.

**Fan settings are inherited, not derived.** `close_fan_the_first_x_layers` `1` and
`full_fan_speed_layer` `3` from `fdm_filament_pla` produce a ramp close to but not equal to
the reference's (fan off on layer 0, 50 % on layer 1, 100 % on layer 2). QIDI Print's fan
curve is Cura's and is per-extruder and per-layer, so §7 of
[`reference/extracted-gcode.md`](reference/extracted-gcode.md) rules it out of scope for a
single-PLA profile. Task 6 will report the difference rather than hide it.

### `support_air_filtration: "0"` — a machine key the filament profile forced out

Adding a filament preset exposed a defect in the machine profile, fixed here. The Qidi
bundle's `fdm_filament_common` sets `activate_air_filtration: "1"`, and
`activate_air_filtration_during_print` defaults to `true`
(`v2.4.2:PrintConfig.cpp:1893`–`1897`). The emission is then gated only on the *machine*
key `support_air_filtration`, which is **absent from the entire QIDI machine chain** and
whose built-in default is `true` (`:3899`–`3903`). The result was two lines the reference
does not have:

```gcode
M106 P3 S255     ; injected after the start block
M106 P3 S0       ; injected *after* ;End of Gcode
```

Neither reference contains any `M106 P<n>`, and no QIDI i-Fast profile documents a
slicer-controlled exhaust fan, so `support_air_filtration: "0"` goes in the machine
profile. Machine-side rather than filament-side deliberately: it is a machine capability,
and this way a stock QIDI filament preset selected against the i-Fast cannot re-introduce
the lines. Tasks 3 and 4 could not have seen this — they sliced without a filament preset,
where `activate_air_filtration` falls back to OrcaSlicer's built-in `false` (`:1886`–`:1890`)
— but any GUI use would have hit it immediately.

### Slicing from the CLI needs a flattened preset

OrcaSlicer's CLI reads each `--load-settings` file **raw and does not resolve `inherits`**
(the handling is commented out in `load_config_file`, `v2.4.2:src/OrcaSlicer.cpp:1953`–`2020`);
missing keys fall back to OrcaSlicer's built-in FFF defaults at `:3629`. A thin preset is
therefore correct in the GUI but loses every inherited QIDI value from the CLI, silently.
Passing the base as a second process file does not help — a duplicate process config is an
error (`:2074`). The task-6 harness flattens the chain itself, keeping the `inherits` key
in its output because the CLI derives `new_printer_system_name` from it.

Two more keys the flattener must **keep**, both learned the hard way: `from`, which is
mandatory and must be `system`, `User` or `user` or the CLI exits `-5` with
`file <x>'s from  unsupported` (`:1975`–`:1979`); and, for a filament preset, `filament_id`
(`:1993`–`:1995`). The filament preset also goes on `--load-filaments`, not
`--load-settings`. The invocation that verified this profile:

```bash
flatpak run com.orcaslicer.OrcaSlicer \
  --load-settings "machine.json;process.json" --load-filaments "filament.json" \
  --slice 0 --export-3mf out.gcode.3mf --outputdir . cube20.stl
```

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
- **`support_air_filtration: "0"`** — otherwise `M106 P3 S255` is injected after the start
  block and `M106 P3 S0` after `;End of Gcode`. See
  [the section above](#support_air_filtration-0--a-machine-key-the-filament-profile-forced-out).
- **`manual_filament_change: "0"`** — OrcaSlicer's own default (`ConfigOptionBool(false)`,
  `v2.4.2:PrintConfig.cpp:5964`–`5970`), restated because getting it wrong is silent and
  total: with it enabled Orca skips `change_filament_gcode` at the first tool change *and*
  turns every `T` into a comment for the entire print (`GCode.cpp:7959`–`7960`;
  `GCodeWriter::toolchange_prefix`, `GCodeWriter.cpp:547`–`551`). The i-Fast is a real
  multi-tool machine, not an M600-and-swap-by-hand one, so it must stay off.

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

## Validation

```bash
bash scripts/validate.sh          # writes out/validate/report.md
```

The harness slices the shipped profiles and diffs the result against
`reference/single-extruder.gcode` and `reference/dual-extruder.gcode`, ignoring
coordinates and comments where the handoff says to. It needs nothing but Python 3, a
`bash`, and an OrcaSlicer install with the QIDI vendor enabled; `out/` is regenerated
from scratch on every run and is gitignored.

| Script | What it does |
|---|---|
| `scripts/validate.sh` | entry point: flatten, generate models, slice, diff, report |
| `scripts/flatten.py` | resolves a preset's `inherits` chain, which the CLI does not |
| `scripts/make_models.py` | writes the test cubes as binary STL |
| `scripts/gcode_diff.py` | the five comparisons |
| `scripts/accepted.py` | the registry of known differences, with a reason for each |

Environment overrides: `ORCA_CMD`, `ORCA_SYSTEM_DIR`, `ORCA_DUAL_CMD`, `DUAL_FILAMENT2`.

### The five checks

1. **Start block** — `;T0` through `M141 S0`, compared **literally**. This block is our
   own `machine_start_gcode` verbatim, so its comments carry meaning and are not
   stripped. A second pass with `S` values normalised distinguishes a temperature-value
   difference from a structural one.
2. **End block** — `M107 T-2` through `;End of Gcode`, also literal.
3. **Temperature commands** — every `M104` / `M109` / `M140` / `M190` / `M141` / `M191`
   line in the file, in order, as a sequence diff plus a per-form count table.
4. **M-codes and G-codes used** — a bare code inventory, and argument forms for M-codes
   and control G-codes (`G0`/`G1` are toolpath and excluded from the form table).
5. **Tool-change sequence** (dual only) — every body `T0`/`T1` with its surrounding
   lines, coordinates normalised, grouped into distinct shapes and compared against the
   three reference variants in
   [`reference/extracted-gcode.md`](reference/extracted-gcode.md) §7.

### How differences are classified

Hard rule 7 of the handoff is "report every difference; do not suppress diffs to make a
check pass", so `scripts/accepted.py` decides a difference's **classification**, never
its visibility. Every difference appears in the report either way.

| Verdict | Meaning | Fails the run? |
|---|---|---|
| **ACCEPTED** | A deliberate, justified deviation, or an artifact of the test fixture. The registry entry names the reason and the document that argues it. | no |
| **KNOWN** | Documented in `TODO.md` but **not settled** — an open question, reported in full every run. This set should shrink. | no |
| **UNEXPECTED** | Not in the registry. A new difference. | **yes** |

The harness is verified to catch a regression: flipping `disable_m73` to `0` surfaces
`M73` as UNEXPECTED in the start block, the end block and the census. It is also
verified deterministic — two runs produce identical reports.

### The dual-extruder case is sliced with OrcaSlicer 2.3.1, not 2.4.2

**The 2.4.2 CLI aborts on any two-filament slice**, with a `std::vector` out-of-range
assertion, before emitting anything. This is an upstream bug, not a defect in these
profiles: it reproduces with OrcaSlicer's own stock `Lulzbot Taz Pro Dual 0.5 nozzle`
preset and with a single-nozzle machine, and it survives every combination of
`--load-filament-ids`, `--arrange`, `--no-check` and hand-supplied extruder-variant
keys. The 2.3.1 AppImage slices the identical flattened presets fine, so the harness
falls back to it for the dual case and says so in the report.

So the dual result is **evidence about the profile's tool-change block, not about
2.4.2's output**. Confirm a two-material job in the 2.4.2 GUI before trusting it; see
`TODO.md`. The single-extruder case is sliced with the target version throughout.

### What the harness reports today

Single-extruder: end block byte-identical; start block differing only in the two
commented-out `T1` heating lines, whose value tracks the second slot's filament. Zero
`M900`, zero `M106 P<n>`, zero `M73`.

Dual-extruder: all 101 body tool changes emit

```gcode
G92 E0                    ; OrcaSlicer's own reset_e() before the change
T0
G92 E0                    ; our change_filament_gcode, verbatim
M109 S200
;_FORCE_RESUME_FAN_SPEED  ; OrcaSlicer re-asserting fan speed
```

which is reference variant C's shape, minus the three documented omissions: the
commented `;M105`, the 8.5 mm retract/prime pair that OrcaSlicer's own retraction owns,
and the `M104 T<old> S150` standby drop deferred to `ooze_prevention`.

Open differences the report lists every run — `G92 E0` 333× against the reference's 7,
OrcaSlicer's extra `G21` / `G90` / `M82`, the reference's unexplained mid-print
`M104 S200`, the spiral Z lift, and our `M109` firing at every tool change where QIDI
Print blocks only when switching to T0 — are all in `TODO.md`.

## Scope

Explicitly out of scope until after a first successful print: tuned retraction, flow
calibration, pressure advance, per-material profiles, chamber-temperature workflows.

Also out of scope, with reasons in `TODO.md`: nozzle sizes other than 0.4 (QIDI
publishes nothing for them, and OrcaSlicer ships no legacy-QIDI process profiles to
derive them from), a material library beyond the one PLA, network printing, and
ooze prevention / idle-nozzle temperature, which only bites once a second material
exists.

## Repository layout

```
profiles/machine/    QIDI i-Fast 0.4 nozzle.json        -> <config>/user/default/machine/
profiles/process/    5 x <layer height> @QIDI i-Fast    -> <config>/user/default/process/
profiles/filament/   QIDI Generic PLA @QIDI i-Fast      -> <config>/user/default/filament/

reference/           read-only inputs, never edited
  single-extruder.gcode, dual-extruder.gcode            QIDI Print exports: ground truth
  extracted-gcode.md                                    the verbatim extraction, with commentary
  qidi-profiles/                                        QIDI's published legacy bundle

scripts/             the validation harness -> out/validate/report.md
  validate.sh  flatten.py  make_models.py  gcode_diff.py  accepted.py

README.md            this file: provenance, install, validation
TODO.md              every unverified value, every open question, every decision
CLAUDE.md            environment and recon notes for anyone picking the work up
ifast-orca-profile-handoff.md   the original spec
LICENSE  NOTICE      AGPL-3.0 and the attribution chain
```

`out/` is validation output, regenerated on every run and gitignored.

## Attribution and license

**This repository is AGPL-3.0.** Full text in [`LICENSE`](LICENSE); the attribution
chain, and which file derives from which upstream preset, in [`NOTICE`](NOTICE).

The short version. The JSONs under `profiles/` are derived works of OrcaSlicer's stock
QIDI vendor profiles, so they inherit OrcaSlicer's licence:

```
Slic3r  ->  PrusaSlicer  ->  Bambu Studio  ->  OrcaSlicer (AGPL-3.0)  ->  this repo
```

Every project in that chain carried its predecessors' work forward under the same
licence and credited them; this one does the same. `LICENSE` is a verbatim copy of
OrcaSlicer `v2.4.2`'s own `LICENSE.txt` (the unmodified GNU AGPL v3 text — same SHA-1).

Everything under `reference/` is **not** ours and is not covered by that: it is QIDI
Technology's own published output — their legacy profile bundle and G-code exported by
QIDI Print — reproduced byte-for-byte as read-only input. `.gitattributes` enforces the
byte-exactness.

This is a community profile, not affiliated with or endorsed by QIDI Technology or the
OrcaSlicer project.

## First print

Single extruder, PLA, small model, supervised, chamber heater off. Get that clean
before trusting anything else in here.

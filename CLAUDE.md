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
| Installed Orca | **flatpak `com.orcaslicer.OrcaSlicer` 2.4.2** (the target). Also AppImages `2.0.0`, `2.2.0`, `2.3.1` in `~/Applications` |
| User config dir | `~/.var/app/com.orcaslicer.OrcaSlicer/config/OrcaSlicer/user/default/{machine,process,filament}/` — **the flatpak sandbox, not `~/.config/OrcaSlicer`** (that tree belongs to the AppImages, schema `01.08.04.51`) |
| Vendors enabled | Anycubic only. **QIDI is not enabled**, so `inherits` will not resolve until the config wizard installs QIDI → X-Max |

**Target version: OrcaSlicer 2.4.2** (decided 2026-09-07). The working tree is a
2.5.0-dev nightly, so pull base profiles from the tag, not the tree:
`git show v2.4.2:"resources/profiles/Qidi/machine/Qidi X-Max 0.4 nozzle.json"`.

Flathub renamed the app to `com.orcaslicer.OrcaSlicer`; the old bundle-installed
`io.github.softfever.OrcaSlicer` had a dead origin and could not be upgraded. The
installed flatpak ships Qidi bundle `02.04.00.06`, and its `Qidi X-Max 0.4 nozzle`,
`fdm_qidi_common`, `fdm_machine_common`, `Qidi X-Max.json` and
`0.20mm Standard @Qidi XMax` are **byte-identical to the `v2.4.2` tag** — verified, so
reading from the tag is safe.

The `v2.4.2 → main` drift in our base chain is one cosmetic rename
(`default_filament_profile`: `"Qidi Generic PLA"` → `"Generic PLA @Qidi"` in
`Qidi X-Max 0.4 nozzle.json`, `Qidi X-CF Pro 0.4 nozzle.json` and
`fdm_qidi_common.json` alike — verified for the X-Max leaf). Nothing else differs, so
working from the tree is *mostly* safe — but the tag is authoritative.

2.4.2 is installed and runs (2026-09-07).

## Recon results (task 1, done)

**Legacy QIDI machines present in the clone** (the only valid base candidates):

| Profile | Build volume | SEMM |
|---|---|---|
| `Qidi X-CF Pro 0.4 nozzle` | 300 × 250 × 300 | `"1"` |
| `Qidi X-Max 0.4 nozzle` | 300 × 250 × 300 | — |
| `Qidi X-Plus 0.4 nozzle` | 270 × 200 × 200 | — |

Everything else in `Qidi/machine/` (X-Max 3/4, X-Plus 3/4/5, X-Smart 3, Q1 Pro, Q2, Q2C)
is Klipper-generation. **Never source values from those.**

**Base profile: `Qidi X-Max 0.4 nozzle`** (changed 2026-09-07 from the X-CF Pro that
task 1 originally recorded). At `v2.4.2` the two leaves are byte-identical apart from
`name`, `setting_id`, `printer_model`, `default_print_profile`, `machine_start_gcode`
and `single_extruder_multi_material` — and X-Max already ships SEMM `"0"` plus a
legacy-QIDI start block that uses `[bed_temperature_initial_layer_single]` and the
`G92 E-19` prime idiom, where X-CF Pro ships SEMM `"1"` and inherits the Prusa-style
block from `fdm_qidi_common`. Both are 300 × 250 × 300, so neither is closer on volume.

**Inherits chain** (machine): `Qidi X-Max 0.4 nozzle` → `fdm_qidi_common` →
`fdm_machine_common` (root, `inherits` absent). Also present but unrelated:
`fdm_qidi_x3_common`, `fdm_q_common`, `fdm_machine_x_common` (Klipper side).

### `single_extruder_multi_material` — why it must be `0`

SEMM `1` describes an MMU-style machine: **one** hotend fed several filaments. The
i-Fast is the other kind — **two** independent hotends. Both `fdm_machine_common` and
`fdm_qidi_common` default to `"1"`, and `Qidi X-CF Pro 0.4 nozzle` keeps it; our base
`Qidi X-Max 0.4 nozzle` is the one legacy leaf that already sets `"0"` (a large part of
why it was chosen). We set it explicitly anyway. The flag is not cosmetic; it changes
four things in the slicer:

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

### How Orca actually emits a tool change (SEMM `0`, prime tower off) — `v2.4.2`

`GCode::set_extruder` (`GCode.cpp:7710`) has **two paths**, and which one runs depends on
how many filaments the *job* uses, not how many the printer has:

- **One filament used** → `m_writer.multiple_extruders` is false and the function
  early-returns at `:7717`–`:7747` with nothing but `m_writer.toolchange(id)`. The custom
  `change_filament_gcode` never runs. This is where the single-extruder GUI slice's extra
  bare `T0` comes from; see "Confirmed by the 2.4.2 GUI slices" below.
  (A *third* path exists but is unreachable for us: with a prime tower the tool change
  goes through `WipeTowerIntegration::append_tcr` (`GCode.cpp:712`+), which processes
  `change_filament_gcode` itself at `:815`/`:972` — it does **not** ignore it, as an
  earlier note in `README.md` claimed. Moot here: a wipe tower requires relative E
  (`Print.cpp:1433`–`1434`), which the reference rules out.)
- **Two filaments used** → the full path, which emits, in order:

1. `this->retract(true, false)` (`:7753`) — **`toolchange=true`**, so it routes through
   `m_writer.retract_for_toolchange()` and uses **`retract_length_toolchange` and
   `retract_restart_extra_toolchange`** (`GCodeWriter.cpp:1015`–`1024`), not
   `retraction_length`. `retract()` internally calls `m_writer.reset_e()`, which in
   absolute-E mode emits `G92 E0`, so Orca's own output is already the reference's
   `G1 F… E<−n>` / `G92 E0` framing. Measured in the 2.4.2 GUI dual slice: 1.82755 mm
   before the wipe + 0.17245 mm during it = exactly the 2 mm `retract_length_toolchange`
   we carry from the base, and a symmetric `G1 E2` prime after the change.
   **This corrects an earlier note here** that claimed `toolchange=false` and that
   `retract_length_toolchange` was unreachable outside the wipe tower. It is reachable,
   which means the reference's 8.5 mm tool-change retract *is* reproducible — as a
   one-key change, with Orca's bookkeeping staying consistent. See `TODO.md`; it is a
   decision for the user, not a defect.
2. a second `this->retract(false, false, LiftType::SpiralLift, true)` at `:7956`, whose
   job is the lift; it is prepended to the parsed `change_filament_gcode`
3. the parsed `change_filament_gcode`
4. `;_FORCE_RESUME_FAN_SPEED`. Note this survives into the output **only after the
   initial tool selection** — for every later change the G-code post-processor replaces
   it with the actual `M106`. Both the 2.3.1 CLI and the 2.4.2 GUI dual files contain
   exactly one of them.
5. `T<n>` — **suppressed** if the custom block already contains a bare `T<next_extruder>`
   at line start (`custom_gcode_changes_tool`, `GCode.cpp:241`, called at `:7992`).
   Suppression is safe: `m_writer.toolchange()` still runs at `:7992` and resets the new
   extruder's E model; only its *string* is discarded.

Useful placeholders: `change_filament_gcode` gets `next_extruder`, `previous_extruder`,
`new_filament_temp` (= first-layer temp on layer 0, else `nozzle_temperature`,
`GCode.cpp:7794`), `old_filament_temp`, `toolchange_count`
(`PrintConfig.cpp:11384`, `11428`+). `machine_start_gcode` gets `is_extruder_used`
(`coBools`, set at `GCode.cpp:2901`–`2904`, before start-G-code processing at `:3022`)
and `bed_temperature_initial_layer_single` (`:3034`). The parser supports
`{cond ? a : b}` and `{if}{else}{endif}` (`PlaceholderParser.cpp:2215`–`2220`).

**`use_relative_e_distances` defaults to `true`** and the whole base chain leaves it
unset — so the explicit `"0"` in our profile is a necessary fix, not documentation.

**Nozzle sizes.** Ship **0.4 only.** It is the sole nozzle QIDI documents for the
i-Fast (`PrusaSlicer_fast.ini`: `nozzle_diameter = 0.4,0.4`), and process values for
other sizes have no source — inventing them breaks rule 1. Adding sizes later is cheap:
Orca's per-nozzle machine profiles are thin overrides that `inherits` the 0.4 profile
and set only `name`, `nozzle_diameter`, `printer_variant` and `default_print_profile`
(see `Qidi X-Max 3 0.6 nozzle.json`, 15 keys). The cost is the *process* profile each
one points at. See `TODO.md`.

**Process chain**: `0.20mm Standard @Qidi XMax` → `fdm_process_qidi_common`
(task 4 inherits the XMax variant now that the machine base changed).
Legacy layer heights available: 0.12 / 0.16 / 0.20 / 0.25 / 0.30, each in
`@Qidi XCFPro`, `@Qidi XMax`, `@Qidi XPlus` variants, gated by `compatible_printers`.

### What Orca actually requires of a user profile (verified at `v2.4.2`)

`PresetCollection::load_presets` (`src/libslic3r/Preset.cpp:1573`–`1770`) is the whole
gate for `<config>/user/default/{machine,process,filament}/*.json`. The cloud-sync path
`load_user_preset` (`:2171`) has different, stricter rules — `setting_id`, `user_id`,
`base_id`, `updated_time` — that **do not apply** to files on disk.

- **`version` is mandatory and must parse as a Semver.** Absent or malformed →
  `continue` with *no log line at all* (`:1653`–`1656`). This is the silent-rejection
  mechanism. Four-component versions work (`deps_src/semver/semver.c:196`–`212`), so use
  the vendor bundle's own `02.04.00.06`. Nothing compares it against the app version.
- **`inherits` must resolve to an already-loaded, `instantiation: "true"` preset.**
  Unresolvable → `can not find parent %1% for config %2%!` and the preset is dropped
  (`:1686`–`1692`). You cannot inherit an abstract base like `fdm_qidi_common`
  (`PresetBundle.cpp:4926`). The vendor must be *enabled* in `OrcaSlicer.conf`'s
  `models` array, or its bundle is deleted from `<config>/system/`
  (`PresetUpdater.cpp:1068`–`1108`).
- **The filename is the preset name**; the `name` key is parsed but never read on this
  path (`:1613`–`1615`). It must not collide with a system preset name (`:1616`–`1621`).
- **Unknown keys are stripped, not fatal** (`remove_invalid_keys`, `:1702`). A key not in
  `Preset::printer_options()` — `s_Preset_printer_options` +
  `s_Preset_machine_limits_options` + `init_extruder_option_keys()` — silently vanishes.
- **A bad *value* for a known key deletes the file** (`:1641`–`1651`). So `profiles/` is
  the source of truth and installing is always a copy.
- `type`, `from`, `instantiation` do **not** gate loading here. Set them anyway to match
  what Orca writes back out (`Preset::save`, `:675`–`686`; `from` ∈ User/Project/Bundle/
  System/Default).
- `printer_model` / `printer_variant` are **not validated** for user presets — that check
  is in the system bundle loader only (`PresetBundle.cpp:4964`–`4999`). A new model name
  is the supported shape; Orca synthesises a `"Custom"` vendor from root user printers
  (`:2394`). Avoid reusing a QIDI model name: `get_current_vendor_type()` (`:612`–`641`)
  would then classify the i-Fast as `VendorType::Klipper_Qidi`.
- `printable_area` is `coPoints` — a JSON array of `"XxY"` strings, 4 corners
  counter-clockwise from the origin. Its `deserialize` **always returns true**, so a
  malformed bed silently becomes degenerate rather than erroring.

## Ground truth from the reference G-code

`reference/single-extruder.gcode` and `reference/dual-extruder.gcode` are **the
authority on machine behavior**. Use their blocks verbatim. Do not tidy them.

**The full verbatim extraction lives in
[`reference/extracted-gcode.md`](reference/extracted-gcode.md) (task 2, done).** That file
is the authority; the notes below are an index into it, not a substitute. Every block there
is reproducible with the `sed` command quoted beside it, and all of them were re-verified
byte-for-byte against the sources.

Headlines:

- Exported by **`Cura_SteamEngine 4.9.1`** (QIDI Print is Cura-derived), `;FLAVOR:Marlin`,
  CRLF. Single: 3628 lines, `M4010` thumbnail on 1-131, G-code header from 132.
  Dual: 11411 lines, thumbnail on 1-458, header from 459, plus a `;SETTING_3` Cura trailer.
- **The reference is absolute-E.** `M82` in the start block and every extrusion move
  carries an absolute `E` (1855 moves single, 7802 dual). `use_relative_e_distances`
  **defaults to `true`** and no profile in the base chain overrides it, so it must be set
  to `0` explicitly. (The `M83` in `fdm_qidi_common`'s start G-code is inherited by the
  X-CF Pro but *not* by our X-Max base, which replaces that block.)
- **`A`/`B` axes appear only in the start block, and only for the prime line.** All
  5 occurrences per file are in the start G-code; the body and the tool change use plain
  `E`. `A` is extruder 0's axis, `B` is extruder 1's, which lets QIDI Print prime both
  hotends without a tool change. **But the `B` value is not constant** — `B19` in the dual
  file, `B0` in the single, tracking whether T1 carries filament. A hardcoded start block
  is wrong for one of the two cases; task 3 has to decide. (An earlier note here claimed
  `B19` unconditionally and that no special handling was needed. That was wrong.)
- M-codes in play: `G0 G1 G28 G92 M82 M84 M104 M106 M107 M109 M140 M141 M190 M2100 M4010`
  - `M4010` — QIDI thumbnail/preview blob; `M4010 X<w> Y<h>` then chunked hex payload
  - `M2100 T<seconds>` — print time estimate for the display
  - `M141 S<n>` — chamber heater. Both references emit `M141 S0`, and it sits *after* the
    prime line, not in the heating order. There is no `M191` anywhere.
  - `M106 T-2 S255` / `M107 T-2` — `T-2` is not an extruder index. Target unidentified;
    `TODO(verify)`, do not guess.
- Heating order in the start block: `M140 S80` → `M104 T0 S200` → `M104 T1 S230` →
  `M190 S80` → `M109 T1 S230` → `M109 T0 S200`. Everything is set first and waited on
  after, so bed and both nozzles heat in parallel. In the single file the two T1 lines are
  present but commented out.
- End block is **15 lines**, not 7: `M107 T-2` / `M140 S0` / `M107` / `M104 S0 T0` /
  `M104 S0 T1` / `M140 S0` (twice, yes) / `;Retract the filament` / `G92 E1` /
  `G1 E-1 F300 Z320` / `G0 F3600 X320 Y0` / `M84` / `M82` / `M104 S0` / `;End of Gcode`.
  Byte-identical between the two files apart from the preceding final retract's E value.
- **Tool change: three variants, 49 of them in the dual file** (25 `T1`, 24 `T0`). All
  share a framing of `G1 F1200 E<current − 8.5>` (an **8.5 mm retract**, not a prime) then
  `G92 E0`. Switching *to* T0 blocks on `M109 S200`; switching *to* T1 does not, and drops
  the parked T0 to `M104 T0 S150` before the `T`. The literal `E8.5` prime comes *after*
  the `T`. The parked hotend's return to 200 °C is issued ~107 lines *earlier*, mid-print,
  outside the tool-change block entirely. Full taxonomy in §7 of the extraction.

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
one — `hot_plate_temp` and `hot_plate_temp_initial_layer` (`v2.4.2` `PrintConfig.cpp:1001`, `1061`),
keyed per bed type. It therefore lives in our generic PLA filament profile, not the
machine profile. Two consequences once a second material is added:

- The print-level enum **`bed_temperature_formula`** decides what a mixed job emits:
  `by_highest_temp` (the **default**, `PrintConfig.cpp` / `GCode.cpp:3531`) takes the max
  across the filaments in the job; `by_first_filament` takes the first extruder's
  (`GCode.cpp:3533`). If every i-Fast filament profile we write says 80, both formulas
  agree and the reference is reproduced either way. Keep it that way unless there is a
  reason not to.
- The start G-code must use the **scalar** placeholder `bed_temperature_initial_layer_single`
  (confirmed at `v2.4.2`, `GCode.cpp:3034`), which is the resolved single value — the
  vector `[bed_temperature_initial_layer]` is per-filament and the wrong shape for a
  two-extruder machine emitting one `M140`. Our X-Max base already uses the scalar form;
  the X-CF Pro, via `fdm_qidi_common`, uses the vector.

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
samples/gui-2.4.2/                     # GUI-sliced evidence the harness cannot produce
scripts/                               # validation harness (task 6)
  validate.sh                          #   entry point: flatten, slice, diff, report
  flatten.py                           #   resolves `inherits`, which the CLI does not
  make_models.py                       #   binary-STL test cubes
  gcode_diff.py                        #   the five comparisons
  accepted.py                          #   registry of known differences, with reasons
ifast-orca-profile-handoff.md          # the spec
README.md                              # provenance: which value came from where
TODO.md                                # every unverified value
LICENSE                                # AGPL-3.0, verbatim from OrcaSlicer v2.4.2
NOTICE                                 # attribution chain + per-file derivation
```

**Packaging (task 7, done.)** `README.md` documents *every* key in the machine profile,
grouped by source, so an audit of `profiles/` against the flattened base turns up nothing
undocumented; keep it that way when adding a key. Attribution lives in three places that
must stay consistent: `NOTICE`, `README.md` §Attribution, and the machine profile's own
`printer_notes` (JSON has no comments). The install instructions in `README.md` are the
procedure that produced the copy under
`~/.var/app/com.orcaslicer.OrcaSlicer/config/OrcaSlicer/user/default/`, which is
byte-identical to `profiles/` — re-verify that after changing a profile.

`.gitignore` excludes `/.idea/`, `*.iml` (JetBrains-opened project), `/out/` for
validation output, and `/00000.log`, the fixed-name log the OrcaSlicer CLI drops in its
working directory. `.gitattributes` protects the byte-exactness of `reference/**`.

## Conventions

- Profile JSONs use **tab indentation** and match Orca's stock key ordering, so diffs
  against the clone's files stay readable.
- Reference G-code and QIDI's published profiles are **read-only inputs**. Never edit them.
  `.gitattributes` marks `reference/**` as `-text -diff` so Git cannot rewrite CRLF line
  endings there — the committed blobs are byte-identical to what QIDI Print produced.
  (Verified: `sha1sum` of worktree and index match for both G-code files.) Do not relax
  this; `core.autocrlf=input` is set on this machine and would otherwise normalise them.
  The one exception is `reference/*.md` — our own commentary, not an input — which is
  re-marked `text eol=lf diff` so it does not get stored as an undiffable binary blob.
- Every value added to a profile gets a line in `README.md` naming its source, or a
  `TODO(verify):` entry in `TODO.md`. A profile that fails loudly beats one that slices
  fine and prints badly.
- OrcaSlicer profiles are AGPL-3.0 and derive from Bambu Studio and PrusaSlicer upstream.
  Preserve that attribution chain in `README.md`.

## Validation (task 6, done)

`bash scripts/validate.sh` → `out/validate/report.md`. Five checks (start block, end
block, temperature commands, code census, tool-change sequence), each difference
classified ACCEPTED / KNOWN / UNEXPECTED by `scripts/accepted.py`; only UNEXPECTED
fails the run, and nothing is ever hidden (hard rule 7). Deterministic across runs, and
verified to catch a regression. Full description in `README.md` §Validation.

The invocations, established empirically — **the flag names below are the ones that
work; `--load_settings` with an underscore is rejected** (`Config.cpp:238` registers
only the dash form, despite the `--help` text):

```bash
# single-extruder — the target version
flatpak run com.orcaslicer.OrcaSlicer \
  --load-settings "machine.json;process.json" --load-filaments "pla.json" \
  --slice 0 --export-3mf out.gcode.3mf --outputdir <dir> cube20.stl

# dual-extruder — one filament id per positional model file
<orca> --load-settings "machine.json;process.json" \
  --load-filaments "pla.json;petg.json" --load-filament-ids "1,2" --arrange 1 \
  --slice 0 --export-3mf out.gcode.3mf --outputdir <dir> cube_a.stl cube_b.stl
```

`--load-filament-ids` sets `ModelObject::config["extruder"]` per *input file*
(`v2.4.2:OrcaSlicer.cpp:1798`–`1807`, `:1839`–`1849`), 1-based, one id per positional
file or `CLI_INVALID_PARAMS`; it is rejected if a `.3mf` is among the inputs
(`:1624`–`1631`). Loading two filaments alone does nothing to the objects — there is no
auto-distribution path in the CLI.

**The flatpak sandbox cannot see `/tmp`.** Every input and output path must live under
the repo (or another location the sandbox can reach), or the slicer reports
`No such file` and exits `-3`.

**The 2.4.2 CLI aborts on *any* two-filament slice** with a `std::vector` out-of-range
assertion. Upstream bug, not ours — it reproduces with OrcaSlicer's own stock
`Lulzbot Taz Pro Dual 0.5 nozzle` preset and with a single-nozzle machine. The harness
falls back to the 2.3.1 AppImage (`ORCA_DUAL_CMD`) for the dual case and labels the
result. Details and the full list of what was ruled out are in `TODO.md`
§"Found by task 6".

Block boundaries used by the harness are unique in all three files: the start block is
`;T0` … `M141 S0` inclusive, the end block `M107 T-2` … `;End of Gcode`, and
OrcaSlicer's `; CONFIG_BLOCK_START` trailer is truncated before any comparison.

## Confirmed by the 2.4.2 GUI slices (2026-09-07)

The user sliced the reference's own 20 mm box by hand in the OrcaSlicer 2.4.2 **GUI**,
once per extruder count. Both files, and what they establish, are in
[`samples/gui-2.4.2/`](samples/gui-2.4.2/README.md). This is the only evidence of GUI
behaviour in the repo — the harness drives the CLI, and the two paths differ.

- **All three presets load and resolve in the GUI**, no substitution: the embedded
  `; CONFIG_BLOCK` names `QIDI i-Fast 0.4 nozzle`, `0.20mm Standard @QIDI i-Fast` and
  `QIDI Generic PLA @QIDI i-Fast`, with 330×250×320, SEMM `0`, absolute E, first layer
  0.3, no prime tower, `disable_m73`, `support_air_filtration 0` and unraised motion
  limits all arriving through `inherits`.
- **`curr_bed_type = High Temp Plate`** — the GUI honours `default_bed_type: "3"` where
  the CLI falls back to Cool Plate, exactly as `README.md` predicted. Both now emit
  `M140 S80`.
- **The 2.4.2 GUI slices two filaments without trouble.** The `std::vector` abort is a
  CLI-only bug. The tool-change block therefore stands confirmed **on the target
  version**: 51/51 body changes emit `T<n>` / `G92 E0` / `M109 S200` in both directions.
- **The `is_extruder_used[1]` conditional works in both directions in the GUI**: the
  single file comments the `T1` heating pair out and primes `B0`; the dual file leaves
  them live and primes `B19`. That is what the two reference files do respectively.
- **New difference — a bare `T0` after the preamble in the single-extruder case.** It
  comes from the one-filament early return in `GCode::set_extruder` (see above). The CLI
  slice of the same profile does not emit it, so the harness is blind to it. Recorded in
  `TODO.md`.

## Definition of done

- Orca loads the profile with no warnings; i-Fast appears with the correct build volume
- Single-extruder slice: start block, end block, and M-codes match the QIDI Print reference
- Dual-extruder slice: tool-change sequence matches the reference
- `TODO.md` lists every unverified value
- `README.md` explains where each setting came from

Explicitly **out of scope** until after a first successful print: tuned retraction, flow
calibration, pressure advance, per-material profiles, chamber-temperature workflows.

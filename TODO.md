# TODO

Every value that is not yet traced to the base OrcaSlicer profile, QIDI's published
profiles, or the reference G-code. Nothing ships with an invented default —
see the "derive, don't invent" rule in [`CLAUDE.md`](CLAUDE.md).

## Next steps

Handoff tasks, with current state. Task 1 is partly done (results in `CLAUDE.md`);
nothing else has been started.

- [x] **1. Recon the schema** — machine/process inherits chains, legacy-vs-Klipper
      machine inventory, user config dir, and the base-profile choice are recorded in
      `CLAUDE.md`. Base: **`Qidi X-Max 0.4 nozzle`** (300×250×300 vs the i-Fast's
      330×250×320; X-CF Pro is the same size, X-Plus is much smaller).
      **Both remaining items are now done** (2026-09-07): the flattened chain is
      recorded in `CLAUDE.md`, and the exact load requirements — including the
      missing-`version` silent skip — are in "What Orca actually requires of a user
      profile". Base changed to **`Qidi X-Max 0.4 nozzle`**; see **Decided**.
- [x] **2. Extract ground truth → [`reference/extracted-gcode.md`](reference/extracted-gcode.md)**
      — done. Verbatim start block, end block, chamber commands, heating order, M-code
      glossary, the full 3-variant tool-change taxonomy, and a mapping onto Orca's
      settings. Every quoted block is reproducible with the `sed` command beside it and
      was re-verified byte-for-byte. The extraction **contradicted five claims** that
      `CLAUDE.md` had recorded from an earlier pass (prime-line `B` value, the
      "prime before the `T`" reading, one-vs-three tool-change variants, the length of
      the end block, and the `[hot_plate_temp_initial_layer]` placeholder name);
      `CLAUDE.md` has been corrected and §9 of the extraction lists them.
- [x] **3. Machine profile** — `profiles/machine/QIDI i-Fast 0.4 nozzle.json` written.
      330×250×320, `nozzle_diameter: ["0.4","0.4"]` + `single_extruder_multi_material: "0"`,
      zero extruder offsets, motion limits byte-identical to the base, and the step-2
      blocks as `machine_start_gcode` / `machine_end_gcode` / `change_filament_gcode`.
      Verified statically *and by slicing with OrcaSlicer 2.4.2*: the profile loads with
      no substitutions and `inherits` resolves; a real single-extruder slice emits an
      **end block byte-identical to the reference**, and a start block identical apart
      from the commented-out `;M104 T1 S<n>` / `;M109 T1 S<n>` pair, whose value tracks
      whatever filament sits in extruder 2 (200 in the test vs the reference's PETG 230)
      and which the machine ignores. The three parked decisions are resolved — see
      **Decided** below.
      **Not yet executed: the tool-change block.** Its shape is derived from the
      `v2.4.2` source, but forcing a body tool change needs a two-material 3MF with
      per-object extruder assignment — task 6's job.
- [x] **4. Process profiles** — five files in `profiles/process/`, one per legacy
      layer height (`0.12mm Fine` / `0.16mm Optimal` / `0.20mm Standard` /
      `0.25mm Draft` / `0.30mm Extra Draft`, each `@QIDI i-Fast`), each a thin override
      of its stock `@Qidi XMax` counterpart. Three keys only:
      `initial_layer_print_height` `0.3`, `enable_prime_tower` `0`, and a
      `compatible_printers` list naming **both** our printer and the base. Speeds and
      line widths are inherited, not imported from Cura, per the handoff.
      All five verified by CLI slice: exit 0, first layer at `Z0.3` over their own
      pitch, no prime tower. Three machine-profile defects were found and fixed in the
      process — see **Found by task 4** below.
- [ ] **5. Filament profile** — one generic PLA inheriting Orca's generic PLA, temps
      from QIDI's reference profile, bed 80 °C (see above).
- [ ] **6. Validate** — derive the Orca CLI invocation from `--help` and the repo docs
      (do not assume flag names). Slice a test model, diff against the reference
      ignoring coordinates and comments, report every difference in the start block,
      end block, temperature commands and M-codes. Repeat for the dual case.
      **2.4.2 is now installed** (flatpak `com.orcaslicer.OrcaSlicer`, 2026-09-07).
- [ ] **7. Package** — fill in `README.md` provenance, finish install instructions,
      confirm the AGPL-3.0 / Bambu Studio / PrusaSlicer attribution chain.

## Open questions for the human

- [ ] **Which head assembly is installed** — standard brass, or the 350 °C high-temp
      variant? Per the handoff we default to the standard brass head, so the profile
      ships `nozzle_type: ["brass","brass"]`; the reference G-code only ever reaches
      230 °C, so it cannot distinguish them. Needs eyes on the machine.
      (Correction: there is **no `nozzle_max_temperature` key at `v2.4.2`** — an earlier
      note here claimed the answer sets one. The real temperature ceiling is the
      filament-side `nozzle_temperature_range_high`, so this question lands on task 5,
      not the machine profile. `nozzle_type` only affects abrasion warnings.)
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
- [x] **Base profile: `Qidi X-Max 0.4 nozzle`**, not `Qidi X-CF Pro 0.4 nozzle`
      (2026-09-07, changed from task 1). At `v2.4.2` the two are byte-identical apart
      from `name`, `setting_id`, `printer_model`, `default_print_profile`,
      `machine_start_gcode` and `single_extruder_multi_material` — and X-Max already
      ships SEMM `"0"` plus a legacy-QIDI start block using
      `[bed_temperature_initial_layer_single]` and the `G92 E-19` prime idiom, where
      X-CF Pro ships SEMM `"1"` and inherits the Prusa-style block from
      `fdm_qidi_common`. Same 300×250×300 volume, so task 1's "closest volume"
      justification is unaffected. Chain is unchanged:
      `Qidi X-Max 0.4 nozzle` → `fdm_qidi_common` → `fdm_machine_common`.
- [x] **Prime-line `B` value: conditional, not a constant.** `machine_start_gcode` uses
      `G1 X330 B{is_extruder_used[1] ? 19 : 0} F2400`, and gates the two `T1` heating
      lines with `{if is_extruder_used[1]}…{else};…{endif}` so they are *commented out*
      exactly as QIDI Print does when T1 is unused. `is_extruder_used` is a real
      start-G-code placeholder (`v2.4.2:GCode.cpp:2901`–`2904`, set before start-G-code
      processing at `:3022`). Verified: the block expands to `single-extruder.gcode` and
      `dual-extruder.gcode` byte-for-byte.
- [x] **Tool change blocks (variant C shape).** `change_filament_gcode` is
      `T{next_extruder}` / `G92 E0` / `M109 S{new_filament_temp}`. The `M109` **must**
      follow the `T` — a `T`-less `M109` addresses the active tool — which is why the
      block owns the `T`. That is safe: `custom_gcode_changes_tool`
      (`v2.4.2:GCode.cpp:241`, called at `:7992`) suppresses only Orca's *emitted* `T`,
      while `m_writer.toolchange()` still runs and resets the new extruder's E model.
- [x] **`use_relative_e_distances: "0"`.** Confirmed necessary, not cosmetic: the option
      **defaults to `true`** (`v2.4.2:PrintConfig.cpp`, `set_default_value(ConfigOptionBool(true))`)
      and the whole base chain leaves it unset, so without an explicit override Orca
      would emit relative E against the reference's `M82`.
- [x] **`printer_model: "QIDI i-Fast"`, a new model name.** User presets are not
      validated against any vendor bundle — that check is in the *system* bundle loader
      only (`v2.4.2:PresetBundle.cpp:4964`–`4999`) — and Orca synthesises a `"Custom"`
      vendor from root user printers (`PresetBundle.cpp:2394`). Reusing `"Qidi X-Max"`
      would have made `get_current_vendor_type()` (`:612`–`641`) classify the i-Fast as
      `VendorType::Klipper_Qidi`, which is wrong (that enum is inert at `v2.4.2`, but
      only by accident). Cost: no vendor bed model/texture — cosmetic.
- [x] **QIDI vendor enabled via the X-Max 3 model** (2026-09-07). The user also owns an
      X-Max 3, so that is what the wizard installed. **This is fine and does not violate
      hard rule 2.** Vendor enablement copies the *whole* `Qidi.json` bundle into
      `<config>/system/` (`PresetUpdater.cpp:1068`–`1108`); the per-model selection only
      controls preset *visibility*, not presence. So the legacy `Qidi X-Max 0.4 nozzle`,
      `fdm_qidi_common` and `fdm_machine_common` are all present and our `inherits`
      resolves — verified by slicing against a copy of the user's real config. The
      Klipper-generation X-Max 3 presets are merely installed alongside; **no value in
      this repo is sourced from them.**
- [x] **First layer height 0.3 mm on every process profile** (2026-09-07). From
      `reference/single-extruder.gcode`, which prints layer 0 at `Z0.3` and later layers
      at `Z0.5 / Z0.7 / Z0.9` — a 0.3 mm first layer over a 0.2 mm pitch. The verbatim
      start block also primes at `G0 X0 Y4 Z0.3`, so 0.3 is the height that hardcoded
      prime line assumes; that is why it applies to **all five** variants and not just
      the 0.20 one. Overrides the stock bases (each sets it equal to its own layer
      height) and QIDI's ini (`first_layer_height = 0.35`). Recorded below.
- [x] **`compatible_printers` lists both printer names** (2026-09-07):
      `["QIDI i-Fast 0.4 nozzle", "Qidi X-Max 0.4 nozzle"]`. Both are needed and they
      are needed by different code paths:
      the GUI's `is_compatible_with_printer` (`v2.4.2:Preset.cpp:837`–`839`) matches
      `active_printer.preset.name`, while the CLI (`OrcaSlicer.cpp:2578`) matches
      `new_printer_system_name`, which is the *machine preset's `inherits` value*
      (`:2045`). `compatible_printers_condition` is not an alternative: the CLI never
      evaluates it, and `is_compatible_with_printer` only falls through to the condition
      when `compatible_printers` is empty (`Preset.cpp:828`).
      Accepted side effect: the five presets also appear under the stock
      `Qidi X-Max 0.4 nozzle` printer in the GUI.
- [x] **Process profiles are thin `inherits` overrides, not flattened** (2026-09-07).
      Idiomatic, and correct in the GUI, which resolves `inherits` properly. The CLI does
      not (see below), so the task-6 harness flattens the chain itself.
- [x] **All five legacy layer heights ship** (2026-09-07): 0.12 / 0.16 / 0.20 / 0.25 /
      0.30, matching the five `@Qidi XMax` process profiles OrcaSlicer `v2.4.2` provides.
      Each is the same three-key override, so the marginal cost over shipping 0.20 alone
      is documentation, not derivation. Only 0.20 is corroborated by reference G-code.
- [x] **Install target: OrcaSlicer 2.4.2 flatpak** (2026-09-07). Flathub renamed the app
      to `com.orcaslicer.OrcaSlicer`; the old bundle-installed
      `io.github.softfever.OrcaSlicer` 2.0.0 had a dead origin and could not be upgraded.
      **User profiles therefore live in
      `~/.var/app/com.orcaslicer.OrcaSlicer/config/OrcaSlicer/user/default/{machine,process,filament}/`**,
      not `~/.config/OrcaSlicer/` (that tree belongs to the AppImages). Verified the
      flatpak ships Qidi bundle `02.04.00.06` and that the whole base chain
      (`Qidi X-Max 0.4 nozzle`, `fdm_qidi_common`, `fdm_machine_common`,
      `Qidi X-Max.json`, `0.20mm Standard @Qidi XMax`) is byte-identical to the
      `v2.4.2` tag.

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

### From task 3 (the machine profile)

- [ ] **`TODO(verify):` the 8.5 mm tool-change retract is not reproduced.** The reference
      retracts 8.5 mm before every tool change and primes 8.5 mm after it. Orca's
      tool-change path calls `retract(toolchange=false, …)`
      (`v2.4.2:GCode.cpp:7956`), so it uses `retraction_length` (2 mm, carried from the
      base) and **`retract_length_toolchange` is unreachable on this path** — it is only
      consumed by the wipe-tower code. Hardcoding the 8.5 mm pair into
      `change_filament_gcode` would leave Orca's retraction bookkeeping 6.5 mm out of
      sync and under-extrude after the next change, so Orca's own symmetric
      retract/unretract owns it instead. Matters for stringing/oozing on a dual-material
      print; harmless for the single-PLA first print. Revisit with a real dual slice.
- [ ] **`TODO(verify):` `machine_max_acceleration_e` is 5000, QIDI publishes 10000.**
      `PrusaSlicer_fast.ini` says `machine_max_acceleration_e = 10000,5000`; the base
      chain gives `5000,5000`. Hard rule 6 (do not raise motion limits) keeps the base
      value. Every other `machine_max_*` matches the ini exactly — this is the lone
      discrepancy.
- [ ] **`TODO(verify):` `nozzle_type: ["brass","brass"]` assumes the standard head.**
      Follows the handoff's "assume the standard head" instruction, not a measurement.
      See the open head-assembly question above. Only affects Orca's abrasion warnings.
- [ ] **`TODO(verify):` forward reference to a filament profile that does not exist yet.**
      `default_filament_profile: ["QIDI Generic PLA @QIDI i-Fast"]` (task 5). Harmless —
      Orca falls back to another preset — but the name must match once task 5 lands.
      (`default_print_profile: "0.20mm Standard @QIDI i-Fast"` now resolves; task 4
      shipped that preset under exactly that name.)

### Found by live-slicing against 2.4.2 (task 3 verification)

Two keys were added to the machine profile as a direct result, and two findings land on
later tasks:

- [x] **`disable_m73: "1"`** — without it Orca injects `M73 P<n> R<n>` progress lines
      *into* the custom start and end blocks. Derived from two independent sources:
      both reference exports contain **zero** `M73`, and QIDI's
      `PrusaSlicer_fast.ini` sets `remaining_times = 0`. With it, the end block is
      byte-identical to the reference.
- [x] **`default_bed_type: "3"`** (= `btPEI`, "High Temp Plate"). Note the **numeric**
      value: `Preset::get_default_bed_type` (`v2.4.2:Preset.cpp:966`–`980`) parses this
      with `atoi`, *not* the `s_keys_map_BedType` name map, so the string
      `"High Temp Plate"` logs `default_bed_type: invalid bed type` on every load. It
      falls back to `btPEI` either way, so this is explicitness, not a behaviour change.
- [ ] **`TODO(verify):` task 5 must set *every* plate-temp variant to 80 °C.**
      `curr_bed_type` defaults to **`btPC` (Cool Plate)**
      (`v2.4.2:PrintConfig.cpp:1080`+), and `default_bed_type` is only read by the GUI
      (`Plater.cpp:2524`–`2538`) — the **CLI never consults it**. So a filament that sets
      only `hot_plate_temp*` slices at `M140 S45` (inherited from `fdm_filament_pla`)
      from the CLI and 80 °C from the GUI. The i-Fast has one physical bed: set
      `cool_plate_temp`, `eng_plate_temp`, `hot_plate_temp`, `supertack_plate_temp`,
      `textured_cool_plate_temp`, `textured_plate_temp` and each `*_initial_layer`
      to 80. Confirmed empirically — doing so produced `M140 S80` / `M190 S80`.
- [x] **The CLI matches `compatible_printers` against the *inherited* preset name.**
      Resolved by task 4 — see **Decided**. Each process profile lists both
      `"QIDI i-Fast 0.4 nozzle"` and `"Qidi X-Max 0.4 nozzle"`. Reproduced empirically:
      a flattened machine profile with `inherits` stripped makes `new_printer_system_name`
      empty and the slice exits `-17 CLI_PROCESS_NOT_COMPATIBLE`.

### Known log noise: `Invalid T command (T1).`

Every slice logs this once, at `error` level. It is **benign, and must not be "fixed"
by changing the start block.**

`GCodeProcessor::process_T` (`v2.4.2:GCode/GCodeProcessor.cpp:5490`–`5494`) rejects any
`T<n>` where `n >= m_result.filaments_count` and skips `process_filament_change`. Our
start block emits `T1` unconditionally — because **the reference does**, in both the
single- and dual-material exports (§2/§3 of the extraction) — but on a single-material
print `filaments_count` is 1, so the *post-processor* refuses it. Confirmed with one and
with two filaments loaded; it is the number of filaments **used**, not loaded, that
counts.

Impact is confined to the G-code processor's estimates: the `T1`/`T0` prime excursion is
not attributed to extruder 1 in the time and filament statistics. The emitted G-code is
unaffected — `T1` is written to the file verbatim (verified), and the immediately
following `T0` re-syncs the processor's tool state, so nothing downstream is wrong.

Gating the `T1` on `is_extruder_used[1]` would silence it, but would deviate from ground
truth: QIDI Print primes both hotends in the start block whether or not T1 carries
filament. Hard rule "use the blocks as-is" wins. The task-6 harness must whitelist this
line.

### Accepted diffs for task 6 introduced by task 3

Deliberate, documented deviations from the reference. The validation harness must report
them, and they must not be "fixed" by making the profile lie:

- `M106 S255` / `M106 S127.5` inside the tool-change block — **omitted**. Fan speed is a
  filament/process property that Orca owns, and Orca appends `;_FORCE_RESUME_FAN_SPEED`
  after `change_filament_gcode` to re-assert it.
- `;_FORCE_RESUME_FAN_SPEED` — an **extra line** Orca emits that the reference has not.
- `;M105` — the commented temperature report in reference variants A and C, omitted.
- `M104 T<old> S150` standby drop — omitted, already deferred to `ooze_prevention` below.
- `G1 F1200 E8.5` prime after the `T` — omitted; see the 8.5 mm retract entry above.

### From task 4 (the process profiles)

- [ ] **`TODO(verify):` `initial_layer_print_height` `0.3` contradicts both the stock
      bases and QIDI's ini.** All five `@Qidi XMax` profiles set it equal to their own
      layer height (0.12 / 0.16 / 0.2 / 0.25 / 0.3); `PrusaSlicer_fast.ini` says
      `first_layer_height = 0.35`. We take the reference G-code's 0.3 because it is the
      authority and because the start block's hardcoded `Z0.3` prime line assumes it.
      Affects first-layer adhesion and squish — check it on the first print.
- [ ] **`TODO(verify):` the four non-0.20 variants have no reference G-code.** Only
      0.2 mm is corroborated by QIDI Print output. The layer heights, speeds and line
      widths of `0.12mm Fine`, `0.16mm Optimal`, `0.25mm Draft` and
      `0.30mm Extra Draft` come from OrcaSlicer's stock legacy-QIDI profiles and are
      unproven on this machine. `0.20mm Standard` is the one to print first.
- [ ] **`TODO(verify):` `z_hop` 0.4 with `z_hop_types` `Auto Lift` has no counterpart in
      the reference.** Carried from the base machine profile. Orca's spiral lift emits
      interpolated Z values (`Z0.357143`, `Z0.414286`, …) between layers; QIDI Print
      emits none — Z is constant across a layer in both references. Not changed here:
      hard rule 6 carries base motion behaviour forward, and tuned retraction is out of
      scope until after a first print. The task-6 harness will see these as diffs.

### Found by task 4 — three defects in the task-3 machine profile

All three were invisible to task 3 because the CLI does not resolve `inherits`, so the
inherited keys never reached the slicer. They are visible in the GUI, which does resolve
it. All three are fixed in `profiles/machine/QIDI i-Fast 0.4 nozzle.json`.

- [x] **`before_layer_change_gcode: ""` — was a hard blocker.**
      `fdm_machine_common` ships `";BEFORE_LAYER_CHANGE\n;[layer_z]\nG92 E0\n"`. With our
      `use_relative_e_distances: "0"` OrcaSlicer refuses to slice at all:
      `"G92 E0" was found in before_layer_change_gcode, which is incompatible with
      absolute extruder addressing`, exit `-51`. Derived from the reference, which has
      **no per-layer `G92 E0`** — every `G92` in `single-extruder.gcode` is in the start
      block (lines 146–174) or the end block (`G92 E1`, line 3622), and neither file
      contains `;BEFORE_LAYER_CHANGE`.
- [x] **`time_lapse_gcode: ""` — output noise.** `fdm_machine_common` ships
      `";TIMELAPSE_TAKE_FRAME\n"`, which OrcaSlicer emits once per layer **even with
      `timelapse_type = 0`** (201 lines in a 20 mm test cube). Neither reference contains
      the marker. Inert on a Marlin machine, but it would have shown up as a diff on
      every layer in task 6.
- [x] **A missing blank line in `machine_start_gcode`.** The reference has an empty line
      between `G0 X5 F2400` and `M141 S0`; our string ran them together. With it restored,
      a real slice reproduces the start block **exactly**, the only remaining diff being
      the six temperature values — which come from the stock `Qidi Generic PLA` filament
      and are task 5's to fix (`M140 S45` / `M104 T0 S210` against the reference's
      `M140 S80` / `M104 T0 S200`).

### Found by task 4 — the CLI does not resolve `inherits`

- [ ] **`TODO(verify):` task 6's harness must flatten the preset chain before slicing.**
      `--load-settings` reads each preset JSON raw: the `inherits`-handling branches in
      the CLI's `load_config_file` are commented out
      (`v2.4.2:src/OrcaSlicer.cpp:1953`–`2020`, see `:1987` and `:1991`), and any key
      absent from the file falls back to OrcaSlicer's built-in FFF default when
      `m_print_config.apply(fff_print_config, true)` runs at `:3629`. A thin preset
      therefore slices correctly in the GUI and silently loses every inherited QIDI value
      from the CLI. Passing the base preset as a second process file is not a workaround —
      the CLI rejects a duplicate process config (`:2074`). The flattener must **keep**
      the `inherits` key in its output: the CLI derives `new_printer_system_name` from it
      (`:2045`), and stripping it makes the compatibility check fail with `-17`.

### From task 2 (the reference G-code extraction)

- [ ] **`TODO(verify):` `M106 T-2 S255` / `M107 T-2` — which fan is `T-2`?** `-2` is not a
      valid extruder index. Both occurrences sit at a `;TIME_ELAPSED` boundary (end of
      layer 0, and the shutdown block), so it is not a per-tool part-cooling fan.
      Candidates are the chamber circulation fan and the auxiliary/side fan. **Do not
      guess** — the user has the machine. Matters because if it is the chamber fan, an
      Orca profile that never emits it will run the enclosure differently from QIDI Print.
- [ ] **`TODO(verify):` `M4010` payload encoding.** `M4010 X<w> Y<h>` followed by
      `M4010 I<offset> T<length> '<hex>'` chunks — a preview bitmap for the display
      (186×186 single, 304×304 dual). Undocumented. Orca cannot emit it. Cosmetic, but
      confirm the printer does not sulk without a preview.
- [ ] **`TODO(verify):` does `M2100 T<seconds>` matter?** Print-time estimate handed to
      the display; matches the `;TIME:` comment exactly. Orca has no equivalent. Confirm
      whether the i-Fast's "time remaining" readout misbehaves without it.
- [ ] **`TODO(verify):` `preheat_time` vs Cura's ramp.** The reference preheats the parked
      hotend ~107 lines before the tool change (`M104 T0 S200`), with interpolated
      intermediate setpoints (`S168.3`, `S155.4`). Orca's `preheat_time` is a different
      model and will not reproduce those values. Only bites once a second material exists.
- [ ] **`TODO(verify):` chamber heater is never used.** Both references emit only
      `M141 S0` and no `M191`. The i-Fast has an actively heated chamber; QIDI Print
      simply does not drive it in these exports. Out of scope per the handoff, noted so
      nobody reads `M141 S0` as "the machine has no chamber heater".

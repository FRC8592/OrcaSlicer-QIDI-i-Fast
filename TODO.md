# TODO

Every value that is not yet traced to the base OrcaSlicer profile, QIDI's published
profiles, or the reference G-code. Nothing ships with an invented default —
see the "derive, don't invent" rule in [`CLAUDE.md`](CLAUDE.md).

## Next steps

Handoff tasks, with current state. Tasks 1–5 are done; validation (6) and packaging (7)
remain.

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
      **The tool-change block has now been executed** (task 6, 2026-09-07). A real
      two-material slice emits, at all 101 body tool changes:
      `G92 E0` / `T<n>` / `G92 E0` / `M109 S<temp>` — Orca's own `reset_e()` framing
      plus our `change_filament_gcode` verbatim, then `;_FORCE_RESUME_FAN_SPEED`.
      That is reference variant C's shape modulo the three documented omissions
      (`;M105`, the 8.5 mm retract/prime pair, the standby drop). Sliced with 2.3.1,
      not the target 2.4.2 — see **Found by task 6** for why.
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
- [x] **5. Filament profile** — `profiles/filament/QIDI Generic PLA @QIDI i-Fast.json`,
      a thin override of the stock `Qidi Generic PLA`. Five things change: nozzle 200 °C
      (both `nozzle_temperature` and `nozzle_temperature_initial_layer`), **all twelve**
      plate-temp keys to 80 °C, `enable_pressure_advance` `0`, and a `compatible_printers`
      list naming both printers. Everything else — diameter, type, flow, fan curve,
      volumetric limit — is inherited, per the handoff's "resist a full material library".
      Verified by CLI slice against 2.4.2: exit 0, the **end block is byte-identical** to
      `single-extruder.gcode`, and the start block differs only in the two *commented-out*
      `;M104 T1 S…` / `;M109 T1 S…` lines (200 here, 230 in the reference, whose second
      slot held PETG — comments the machine ignores). Zero `M900`, zero `M106 P3`.
      One machine-profile defect was found and fixed in the process — see
      **Found by task 5** below.
- [x] **6. Validate** — `scripts/validate.sh` flattens the presets, generates the test
      models, slices both cases and diffs the output against the references, writing
      `out/validate/report.md`. Five checks (start block, end block, temperature
      commands, code census, tool-change sequence); every difference is reported and
      classified ACCEPTED / KNOWN / UNEXPECTED against `scripts/accepted.py`, and only
      an UNEXPECTED one fails the run. Verified deterministic across runs, and verified
      to *catch* a regression (flipping `disable_m73` to `0` surfaces `M73` as
      UNEXPECTED in the start block, the end block and the census).
      Current state: **0 unexpected** in both cases. The single case reproduces task 5's
      hand result exactly — end block byte-identical, start block differing only in the
      two commented-out `T1` lines. **The tool-change block is now executed**, which
      task 3 could not do; see **Found by task 6** below.
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
      **Task 5 does not settle it and does not need to:** the PLA profile inherits
      `nozzle_temperature_range_high` `240`, far below either head's rating, so PLA
      cannot tell the two apart. The answer only starts to matter when a material above
      240 °C is added.
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

- [x] **Filament profile: one preset, `QIDI Generic PLA @QIDI i-Fast`** (2026-09-07),
      inheriting `Qidi Generic PLA` → `fdm_filament_pla` → `fdm_filament_common`. Five
      overrides only. Per the handoff: "Resist producing a full material library — that's
      tuning work that belongs after the machine is proven."
- [x] **Nozzle 200 °C, first layer and body alike.** Two independent sources agree:
      `M104 T0 S200` / `M109 T0 S200` in both references, and
      `temperature = 200` / `first_layer_temperature = 200` in `PrusaSlicer_fast.ini`.
      The single reference's one mid-print `M104 S200` re-asserts the same value, so
      there is no first-layer/body split to reproduce.
- [x] **`enable_pressure_advance: ["0"]`.** The parent ships `1` with
      `pressure_advance: 0.031`, which on a `marlin` flavor emits `M900 K0.031`
      (`v2.4.2:GCodeWriter.cpp:388`–`389`). There is **no `M900` anywhere** in either
      reference export, in `PrusaSlicer_fast.ini`, or in the Simplify3D `.fff` — so the
      0.031 has no i-Fast provenance, and the handoff puts pressure advance out of scope
      until after a first print. `pressure_advance` itself is left inherited (unused) so
      the number survives for later tuning. See the `TODO(verify)` below.
- [x] **Fan settings stay inherited.** `fdm_filament_pla` gives
      `close_fan_the_first_x_layers` `1` and `full_fan_speed_layer` `3`, close to but not
      equal to the reference's off/50 %/100 % ramp over layers 0–2. §7 of the extraction
      already ruled QIDI Print's per-extruder, per-layer Cura fan curve out of scope for a
      single-PLA profile. Recorded as an accepted diff below rather than reverse-engineered.

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
- [x] **Resolved: `default_filament_profile` now points at a preset that exists.**
      `["QIDI Generic PLA @QIDI i-Fast"]` — task 5 shipped the filament preset under
      exactly that name, so both `default_*_profile` forward references resolve.

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
- [x] **Resolved by task 5: *every* plate-temp variant is set to 80 °C.**
      `curr_bed_type` defaults to **`btPC` (Cool Plate)**
      (`v2.4.2:PrintConfig.cpp:1080`+), and `default_bed_type` is only read by the GUI
      (`Plater.cpp:2524`–`2538`) — the **CLI never consults it**. So a filament that sets
      only `hot_plate_temp*` slices at `M140 S45` (inherited from `fdm_filament_pla`)
      from the CLI and 80 °C from the GUI. The i-Fast has one physical bed: set
      `cool_plate_temp`, `eng_plate_temp`, `hot_plate_temp`, `supertack_plate_temp`,
      `textured_cool_plate_temp`, `textured_plate_temp` and each `*_initial_layer`
      to 80. Confirmed empirically — doing so produced `M140 S80` / `M190 S80`.
      All twelve keys are in the shipped filament profile.
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

Introduced by task 5:

- **Fan ramp.** Reference: `M107` on layer 0, `M106 S127.5` (50 %) on layer 1,
  `M106 S255` (100 %) on layer 2. Ours: OrcaSlicer's own ramp from
  `close_fan_the_first_x_layers` `1` and `full_fan_speed_layer` `3`. Same shape, different
  numbers. Deliberate — see **Decided**.
- **`M900` absent.** The reference has none and neither do we, but note that this is a
  *deviation from the stock `Qidi Generic PLA`*, not from the reference. Task 6 should
  confirm zero `M900` rather than treat its absence as untested.

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

- [x] **Done in task 6: `scripts/flatten.py` flattens the preset chain before slicing.**
      Verified to reproduce the hand-built `machine.json` task 5 sliced with, key for key.
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

### From task 5 (the filament profile)

- [ ] **`TODO(verify):` pressure advance is switched off, against the stock preset.**
      `enable_pressure_advance: ["0"]`. The stock `Qidi Generic PLA` — which *is* declared
      compatible with the legacy `Qidi X-Max 0.4 nozzle` — enables it at `K0.031`, so
      OrcaSlicer's own vendor believes a legacy QIDI board accepts `M900`. We disable it
      because no QIDI i-Fast source emits `M900` and because PA is explicitly out of scope
      per the handoff. Two things to check after a first print: whether the Chitu board
      actually implements `M900`, and whether 0.031 is anywhere near right for this
      extruder. Turning it back on is a one-key change.
- [ ] **`TODO(verify):` `filament_flow_ratio` `0.98` is inherited and contradicts QIDI.**
      `PrusaSlicer_fast.ini` says `extrusion_multiplier = 1,1`. Both are sourced values,
      so neither is an invention; we keep the inherited 0.98 because the handoff scopes
      flow calibration out until after a first print. Worth 2 % of extrusion — check it
      on the first print before tuning anything else.
- [ ] **`TODO(verify):` the fan curve is OrcaSlicer's, not QIDI's.** See **Decided** and
      the accepted-diffs list. Affects overhangs and bridging on PLA.
- [ ] **`TODO(verify):` bed 80 °C is high for PLA.** It is what QIDI Print emits on this
      machine for both PLA and PLA + PETG (see `CLAUDE.md`), and G-code beats the ini's
      60 °C by rule — but 80 °C is at the top of the usual PLA range and elephant's foot
      is the thing to watch on the first print. `PrusaSlicer_fast.ini`'s 60 °C is the
      dissenting source.

### Found by task 5 — one defect in the machine profile

- [x] **`support_air_filtration: "0"` added to the machine profile.** Without it, a slice
      *with any QIDI filament preset* emits two lines the reference does not have:
      `M106 P3 S255` after the start block and `M106 P3 S0` **after `;End of Gcode`**.
      Chain: the Qidi bundle's `fdm_filament_common` sets `activate_air_filtration: "1"`;
      `activate_air_filtration_during_print` defaults to `true`
      (`v2.4.2:PrintConfig.cpp:1893`–`1897`); and the emission
      (`GCode.cpp:3181`–`3197`, `:3501`–`:3514`) is gated only on the **machine** key
      `support_air_filtration`, which is **absent from the whole QIDI machine chain** and
      defaults to `true` (`PrintConfig.cpp:3899`–`3903`). Neither reference contains any
      `M106 P<n>` and no QIDI i-Fast profile documents a slicer-driven exhaust fan.
      Fixed machine-side, not filament-side, because it is a machine capability — this way
      a *stock* QIDI filament selected against the i-Fast cannot re-introduce the lines.
      Tasks 3 and 4 could not have caught it: they sliced with no filament preset, where
      `activate_air_filtration` falls back to OrcaSlicer's built-in `false`
      (`PrintConfig.cpp:1886`–`1890`). Any GUI use would have hit it on the first slice.
      **This weakens task 3's "end block byte-identical" claim as it stood** — that was
      true of a filament-less CLI slice only. It is true again now, with the filament
      preset loaded and this key set (re-verified 2026-09-07).

### Found by task 5 — `M201`/`M203`/`M204`/`M205`, not yet decided

- [ ] **`TODO(verify):` OrcaSlicer emits four machine-limit M-codes the reference has not.**
      Immediately before the start block every slice writes
      `M201 X9000 Y9000 Z500 E5000`, `M203 X500 Y500 Z12 E120`, `M204 P1500 R1500 T1500`
      and `M205 X10.00 Y10.00 Z0.20 E2.50`. The *values* are fine — they are the base
      profile's `machine_max_*`, which match `PrusaSlicer_fast.ini` exactly (see the
      `machine_max_acceleration_e` entry above for the one exception). What is undecided
      is whether they should be **emitted at all**: QIDI Print writes none of them, so the
      i-Fast prints today with whatever the firmware has stored. `machine_limits_usage`
      is absent from our profile and from the whole QIDI chain, so Orca's default
      ("emit to G-code") applies; setting it to time-estimate-only would suppress them.
      Left alone deliberately — this is a machine-profile question with a real argument
      either way, and the lines are standard Marlin, not QIDI-specific. **Ask the user
      before changing it** (rule 8: the machine is in front of them). Task 6 must report
      these four lines as a diff.

### Found by task 5 — two more CLI flattener requirements

- [x] **Done in task 6: the flattener keeps `from` and `filament_id`, and the harness
      uses `--load-filaments`.**
      Two additions to the task-4 finding below. `from` is **mandatory** in every
      `--load-settings` file and must be `system`, `User` or `user`; stripping it exits
      `-5` with `file <x>'s from  unsupported` (`v2.4.2:src/OrcaSlicer.cpp:1975`–`1979`).
      A filament preset goes on `--load-filaments`, not `--load-settings`, and its
      `filament_id` is read from the same key-value map (`:1993`–`1995`), so keep that too.
      The invocation that verified task 5:
      ```bash
      flatpak run com.orcaslicer.OrcaSlicer \
        --load-settings "machine.json;process.json" --load-filaments "filament.json" \
        --slice 0 --export-3mf out.gcode.3mf --outputdir . cube20.stl
      ```

### Found by task 6 (the validation harness)

Everything here came out of `scripts/validate.sh`. The report that produced it is
regenerated by re-running the script; `out/` is gitignored.

#### The OrcaSlicer 2.4.2 CLI cannot slice a two-filament job at all

- [ ] **`TODO(verify):` upstream bug, not ours — the dual case is validated on 2.3.1.**
      Any invocation passing two `--load-filaments` entries to the 2.4.2 flatpak aborts
      before emitting anything:

      ```
      stl_vector.h:1282: const_reference std::vector<int>::operator[](size_type) const:
      Assertion '__n < this->size()' failed.
      ```

      It is **not** caused by this profile. Reproduced with, in order of how conclusive
      each is:
      - OrcaSlicer's own stock `Lulzbot Taz Pro Dual 0.5 nozzle` machine preset (a
        shipping 2.4.2 dual-extruder profile whose shape matches ours — `nozzle_diameter`
        of 2, `single_extruder_multi_material` `0`, and no extruder-variant keys either);
      - a copy of our machine preset cut down to **one** nozzle;
      - with and without `--load-filament-ids`, with and without `--arrange`,
        with `--no-check`, and with the extruder-variant keys
        (`extruder_variant_list`, `printer_extruder_variant`, `printer_extruder_id`,
        `extruder_type`, `nozzle_volume_type`) and `filament_map` supplied by hand.

      The crash is inside slicing, after `Print::validate()` (a prime-tower run gets as
      far as the `-51` wipe-tower rejection first) and after
      `update_values_to_printer_extruders_for_multiple_filaments`. It reaches ~35 %
      progress and dies in a parallel worker, so the debug log does not localise it.
      The **2.3.1 AppImage slices the identical flattened presets without complaint**
      (101 body tool changes), so `scripts/validate.sh` falls back to it for the dual
      case and labels the result. Worth re-testing on the next OrcaSlicer release; if a
      later version fixes it, drop `ORCA_DUAL_CMD` from the harness.
      Consequence to keep in mind: **the dual-extruder evidence is about the profile's
      tool-change block, not about 2.4.2's output.** The single-extruder case is sliced
      with the target version.

- [ ] **`TODO(verify):` the GUI's dual behaviour on 2.4.2 is untested.** The crash is on
      the CLI path, which does not call `Preset::normalize` and so never runs
      `set_num_extruders` → `extend_extruder_variant`
      (`v2.4.2:PrintConfig.cpp:8797`, `:8831`). The GUI does. Whether that is what makes
      the difference is unproven — supplying those keys by hand did not stop the CLI
      crash. Before the first two-material print, slice a two-material job **in the GUI**
      on 2.4.2 and confirm the tool-change block comes out as the harness reports it.

#### Differences the harness reports every run, still unresolved

These are classified KNOWN: documented here, printed in full in the report, and not
failing the run. They should shrink over time.

- [ ] **`TODO(verify):` `G92 E0` 333 times against the reference's 7.** OrcaSlicer resets
      the extruder datum after every retraction and wipe; QIDI Print's absolute `E`
      climbs monotonically for the whole print and only resets in the start and end
      blocks. Under `M82` the two are functionally equivalent — each `G92 E0` just
      re-bases the following absolute values — and this is standard PrusaSlicer/Orca
      behaviour that prevents `E` overflow on long prints. Unverified on the Chitu board.
- [ ] **`TODO(verify):` OrcaSlicer emits `G21` and `G90`, and a second `M82`.** Right
      after our start block: `G90` (absolute positioning), `G21` (millimetres) and
      `M82 ; use absolute distances for extrusion`. The reference has no `G21` and no
      `G90` at all, and only the one `M82` our own block emits. All three are standard
      Marlin and all three restate what the machine is already doing, but no QIDI source
      emits them.
- [ ] **`TODO(verify):` the reference re-asserts `M104 S200` once mid-print; we do not.**
      Same value the start block already set, emitted between two extrusion moves. No
      behavioural difference is expected. Unexplained.
- [ ] **`TODO(verify):` the spiral Z lift shows up as `G17` + `G3` on 2.3.1.** 99 of each
      in the dual output, from `z_hop_types` `Auto Lift` carried out of the base machine
      profile. `enable_arc_fitting` is `0`, so these are the lift itself, not arc-fitted
      toolpaths — and note 2.4.2 emits the same lift as `G1` segments instead. QIDI Print
      emits neither. This is the same open question as the existing `z_hop` entry above,
      now with the exact G-codes attached: **confirm the Chitu firmware accepts `G2`/`G3`
      before running a dual job sliced on 2.3.1.**

#### Corroborated by task 6

- [x] **`enable_prime_tower: "0"` is load-bearing, and now proven.** Turning it on makes
      2.4.2 refuse the slice outright: `The Wipe Tower is currently only supported with
      the relative extruder addressing (use_relative_e_distances=1)`, exit `-51`. Our
      absolute-E requirement and a prime tower are mutually exclusive, independently of
      the `WipeTowerIntegration` argument already recorded in `README.md`.
- [x] **`M900` really is absent from our own output.** Task 5 asserted it; the census now
      counts it: zero `M900` in the single-extruder slice. The 50 `M900 K0.04` lines in
      the dual output come from the **PETG test fixture**, which leaves
      `enable_pressure_advance` on — not from anything this repo ships.

#### The dual-extruder test fixture

The dual case slices two cubes with our PLA on extruder 1 and OrcaSlicer's stock
`Qidi Generic PETG` on extruder 2, matching the reference job's PLA + PETG. That preset
is a **fixture only**: it is not in `profiles/`, and no value in this repo is sourced
from it. Its own settings therefore leak into the comparison, and the harness reports
them as fixture artifacts rather than profile defects:

- `M900 K0.04` — the fixture leaves pressure advance enabled.
- `M140 S60 ; set bed temperature` and one extra `M140` — the fixture's
  `cool_plate_temp` is 60 °C against our 80 °C. This is exactly the
  `bed_temperature_formula` question already deferred above; every filament preset this
  repo ships says 80, so it cannot arise from our own profiles.
- `M104 T1 S240` in the start block and `M109 S250` at tool changes — the fixture's PETG
  temperatures, against the reference's PETG at 230 °C.
- Tool-change *count* (101 vs the reference's 49) — a property of the test model, two
  cubes alternating every layer, not of the profile.

`DUAL_FILAMENT2` overrides the fixture if a better second material turns up.

#### Confirmed: our tool change blocks in both directions, the reference does not

- [ ] **`TODO(verify):` `M109` fires at every tool change; QIDI Print blocks only for T0.**
      `change_filament_gcode` is variant C's shape, so every switch waits for
      temperature. The reference blocks on `M109 S200` when switching **to T0** (variant
      C, 24×) but not on later switches to T1 (variant B, which relies on T1 already
      being hot). Ours therefore emits 103 `M109` against the reference's 27. One string
      cannot be both, and task 3 chose the safe one deliberately — but it costs a
      temperature wait on every change, which will slow a dual print. Revisit if the
      first dual print is unacceptably slow.
- [ ] **`TODO(verify):` OrcaSlicer's lookahead preheat is annotated and differently
      scheduled.** Ours: `M104 S200 T0 ; preheat T0 time: 30s`, 49×. The reference:
      a bare `M104 T0 S200` about 107 lines ahead of the change, with interpolated
      intermediate setpoints. Same idea, different model — as the existing
      `preheat_time` entry predicted. Only matters once a second material ships.

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

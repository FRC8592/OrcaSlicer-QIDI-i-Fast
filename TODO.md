# TODO

Every value that is not yet traced to the base OrcaSlicer profile, QIDI's published
profiles, or the reference G-code. Nothing ships with an invented default —
see the "derive, don't invent" rule in [`CLAUDE.md`](CLAUDE.md).

One section — **WiFi upload to the i-Fast** — is not about a sliced value at all. It is
the live list for [`intent/0003`](intent/0003-wifi-upload-to-the-ifast.md), kept here
because this file is where open work lives.

## Next steps

The seven tasks, with current state
([`intent/0001`](intent/0001-orcaslicer-profile-for-the-ifast.md) §"How the work was
decomposed"). **All seven are done**, and a **first-print review**
(2026-09-07) has since brought the print body's motion, the idle-nozzle temperature and
one fan command into line with the reference — see **Found by the first-print review**
below.

Then the printing started. Single-head prints came off fine; **the first dual print
failed** (2026-09-12), and the tool-change block has been rewritten around a park and a
purge as a result — see **Found by the first dual print** below, and
[`intent/0004`](intent/0004-make-the-dual-extruder-print-work.md). That rewrite has
**not yet been executed by a slicer**: it needs a 2.4.2 GUI slice of a two-cube job,
because the CLI cannot slice two filaments and no fallback exists on this machine.
That is the next thing to do.

Also open, and not slicer work: the two heads are **not aligned in XY** — visible in the
control print, so it is a firmware calibration, not ours — plus the physical checks listed
under **Open questions for the human** and **Unverified profile values** below. Running
alongside, and independent of all of it, is **WiFi upload to the i-Fast** — getting sliced
G-code to the machine without a USB stick.

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
      line widths are inherited, not imported from Cura, per the project scope.
      All five verified by CLI slice: exit 0, first layer at `Z0.3` over their own
      pitch, no prime tower. Three machine-profile defects were found and fixed in the
      process — see **Found by task 4** below.
- [x] **5. Filament profile** — `profiles/filament/QIDI Generic PLA @QIDI i-Fast.json`,
      a thin override of the stock `Qidi Generic PLA`. Five things change: nozzle 200 °C
      (both `nozzle_temperature` and `nozzle_temperature_initial_layer`), **all twelve**
      plate-temp keys to 80 °C, `enable_pressure_advance` `0`, and a `compatible_printers`
      list naming both printers. Everything else — diameter, type, flow, fan curve,
      volumetric limit — is inherited, per the brief's "resist a full material library".
      Verified by CLI slice against 2.4.2: exit 0, the **end block is byte-identical** to
      `single-extruder.gcode`, and the start block differs only in the two *commented-out*
      `;M104 T1 S…` / `;M109 T1 S…` lines (200 here, 230 in the reference, whose second
      slot held PETG — comments the machine ignores). Zero `M900`, zero `M106 P3`.
      One machine-profile defect was found and fixed in the process — see
      **Found by task 5** below.
- [x] **6. Validate** — `scripts/validate.sh` flattens the presets, generates the test
      models, slices both cases and diffs the output against the references, writing
      `out/validate/report.md`. Five checks at the time (start block, end block,
      temperature commands, code census, tool-change sequence; the first-print review
      added motion envelope and tool-change priming); every difference is reported and
      classified ACCEPTED / KNOWN / UNEXPECTED against `scripts/accepted.py`, and only
      an UNEXPECTED one fails the run. Verified deterministic across runs, and verified
      to *catch* a regression (flipping `disable_m73` to `0` surfaces `M73` as
      UNEXPECTED in the start block, the end block and the census).
      Current state: **0 unexpected** in both cases. The single case reproduces task 5's
      hand result exactly — end block byte-identical, start block differing only in the
      two commented-out `T1` lines. **The tool-change block is now executed**, which
      task 3 could not do; see **Found by task 6** below.
- [x] **7. Package** — done (2026-09-07). `README.md` now documents **every key** in
      the machine profile, grouped by source (preset metadata / geometry / motion limits
      / per-extruder arrays / G-code blocks / forced by OrcaSlicer), so nothing in
      `profiles/` is undocumented; the previously unexplained keys were
      `manual_filament_change`, `nozzle_type`, `printer_notes`, `printer_variant`, the
      two `default_*_profile` forward references and the fourteen per-extruder arrays.
      Install instructions gained prerequisites, a post-install confirmation checklist,
      log locations, and update/uninstall steps. `LICENSE` (a verbatim copy of
      OrcaSlicer `v2.4.2`'s own AGPL-3.0 text, same SHA-1) and `NOTICE` (the
      Slic3r → PrusaSlicer → Bambu Studio → OrcaSlicer → here chain, plus which file
      derives from which upstream preset) are new. `README.md` also gained a repository
      layout map. See **Found by task 7** below for what packaging checked.

## Open questions for the human

- [x] **Done: the profile loads and slices in the 2.4.2 GUI** (2026-09-07). The user
      sliced the reference's own 20 mm box twice by hand; both files are in
      [`samples/gui-2.4.2/`](samples/gui-2.4.2/README.md). The embedded `; CONFIG_BLOCK`
      names all three of our presets with no substitution and shows every value arriving
      through `inherits` — 330×250×320, SEMM `0`, absolute E, first layer 0.3, no prime
      tower, motion limits unraised. See **Found by the 2.4.2 GUI slices** below.
      Residual, minor: nobody has read the GUI's *log* for warnings. The G-code proves
      the presets resolved; it does not prove the log is clean.

- [x] **Done (2026-09-07): `samples/gui-2.4.2/` re-sliced with the current profile.**
      Both new files carry the review's values in their `; CONFIG_BLOCK` and body — no
      `F30000`, no `M20x`, no lift, 1.5 mm @ `F1800` retracts, `M106 T-2 S255` once at
      layer 1, and on the dual file ooze prevention's cooldown/preheat lines with 0 mm
      retract debt at all 51 tool changes. `samples/gui-2.4.2/README.md` lists it all.

- [ ] **First print: watch for a lift/park cycle before the first layer.** The
      single-extruder GUI slice emits a bare `T0` between the start block's prime line
      and the first layer — after OrcaSlicer's `G90`/`G21`/`M82` preamble — which neither
      the QIDI Print reference nor a CLI slice contains. T0 is already the active tool, so
      it should be a no-op, but **head auto-lift is firmware behaviour triggered by tool
      changes** and nobody has watched what this firmware does with a redundant `T0`.
      What to look for: does the head lift, park, or pause between priming at
      `X0 Y4 Z0.3` and starting layer 1? If it does, say so — it is fixable, but not by
      editing the start block: OrcaSlicer emits the line itself, afterwards. Mechanism
      and code references under **Found by the 2.4.2 GUI slices**.

- [ ] **First print: which fan comes on as layer 1 starts?** The profile now reproduces
      the reference's `M106 T-2 S255` there (see **Decided**), without knowing what `T-2`
      addresses. Chamber circulation, exhaust, or a side blower — note which. If it is a
      part-cooling fan, the command matters for PLA overhangs; if it is the chamber
      circulation fan, it matters for the enclosure. Either way it is what QIDI Print does.

- [ ] **Which head assembly is installed** — standard brass, or the 350 °C high-temp
      variant? Per the brief we default to the standard brass head, so the profile
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
      overriding the 60 °C in QIDI's `prusaslicer/PrusaSlicer_fast.ini` (see
      [`reference/qidi-profiles.md`](reference/qidi-profiles.md)).
      G-code is ground truth. Record the discrepancy in `README.md`.
- [x] **`A`/`B` extruder axes: not an issue.** All 5 occurrences in each reference file
      are inside the start block's prime line; the print body and the tool change use
      plain `E`. Since the start block is pasted verbatim, nothing special is needed.
- [x] **`single_extruder_multi_material: "0"`**, paired with
      `nozzle_diameter: ["0.4","0.4"]` — the flag alone does not change the extruder
      count. Full reasoning in `CLAUDE.md`.
- [x] **No prime/wipe tower — and it cannot be enabled on 2.4.2** (asked and answered
      2026-09-07). `Print::validate` refuses the slice outright with *"The Wipe Tower is
      currently only supported with the relative extruder addressing
      (use_relative_e_distances=1)"* (`v2.4.2:Print.cpp:1433`–`1434`, exit `-51`;
      reproduced by the task-6 harness). Our absolute E is not a preference — it is what
      the reference does on every extrusion move — so a tower and fidelity to QIDI Print
      are mutually exclusive at this version.
      If it is ever wanted, the cost is not just the `use_relative_e_distances` flip: the
      tool change would move off `GCode::set_extruder` onto
      `WipeTowerIntegration::append_tcr` (`GCode.cpp:712`+), which processes
      `change_filament_gcode` itself (`:815`, `:972`) with its own retraction and
      temperature handling, so the whole tool-change block would need re-validating.
      (This corrects an earlier note in `README.md` which said `change_filament_gcode`
      "never runs" with a tower. It does run — by a different route.)
      QIDI's own answer to ooze on this machine is not a tower: an 8.5 mm tool-change
      retract and a standby temperature drop. Both are already recorded — see the
      retract entry under task 3 and **Deferred until a second material exists**.
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
      overrides only. Per the brief: "Resist producing a full material library — that's
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
      0.031 has no i-Fast provenance, and the project scope puts pressure advance out
      of scope until after a first print. `pressure_advance` itself is left inherited
      (unused) so the number survives for later tuning. See the `TODO(verify)` below.
- [x] **Fan settings stay inherited.** `fdm_filament_pla` gives
      `close_fan_the_first_x_layers` `1` and `full_fan_speed_layer` `3`, close to but not
      equal to the reference's off/50 %/100 % ramp over layers 0–2. §7 of the extraction
      already ruled QIDI Print's per-extruder, per-layer Cura fan curve out of scope for a
      single-PLA profile. Recorded as an accepted diff below rather than reverse-engineered.

- [x] **Match QIDI Print's motion for the first print** (2026-09-07, user). The base
      OrcaSlicer profile asked the machine for things the reference never does; each is
      now set to what the reference G-code shows, with QIDI's Cura definition
      (`CURA/qidi.zip:qidi/definitions/qidi.def.json` in QIDI's published bundle — see
      [`reference/qidi-profiles.md`](reference/qidi-profiles.md)) as the
      corroborating source, and none of it is a *tuned* value:
      - `travel_speed` **100** (was 500 from `0.20mm Standard @Qidi XMax`; reference
        `F6000`, Cura `speed_travel 100`, ini 130 — see the `TODO(verify)` below);
      - `retraction_length` **1.5**, `retraction_speed` **30**, `wipe` **0** (reference:
        50 retractions of exactly 1.5 mm at `F1800`, none during a move; ini `wipe = 0`);
      - `z_hop` **0** (reference: Z constant within a layer; ini `retract_lift = 0`);
      - `travel_speed_z` **5** (reference: every Z-carrying move at `F300`; Cura
        `speed_z_hop 5`);
      - `emit_machine_limits_to_gcode` **0** and `default_acceleration` /
        `default_jerk` **0** (reference: no `M201`/`M203`/`M204`/`M205` at all).
      Per-feature *printing* speeds were already the reference's and are untouched.
      The harness's new motion-envelope check keeps all of this equal to the reference,
      and its registry deliberately has no entry for any of it.
- [x] **Ooze prevention enabled now, not deferred** (2026-09-07, user). `ooze_prevention`
      `1` on all five process profiles, `idle_temperature` `150` on the PLA filament,
      from the reference's `M104 T0 S150` (27×). `preheat_time` stays at Orca's default
      30 s: at QIDI's stated 1.6 °C/s heat-up (Cura `machine_nozzle_heat_up_speed`)
      150 → 200 takes ~31 s. What it does to a multi-material job is written up in
      `README.md` §Filament profile; the short version is that the parking temperature
      is per filament, nothing moves, the start block is untouched, and OrcaSlicer's
      post-processor drops cooldowns for short idles (`; removed M104`) much as Cura
      parked only T0. Executed in the 2.3.1 harness dual case **and confirmed in a
      2.4.2 GUI dual slice** (`samples/gui-2.4.2/20mm_Box_PLA_15m3s_multi.gcode`): four
      `M104 S150 T1 ;cooldown`, eight preheats, `M109 S200 T<n>` after every change.
- [x] **`M106 T-2 S255` reproduced at layer 1** (2026-09-07, user), via
      `layer_change_gcode` = `{if layer_num == 1}M106 T-2 S255\n{endif}`. Both references
      emit it once at the layer 0 → 1 boundary and both end blocks already emitted
      `M107 T-2` — the profile was switching off a fan it never switched on. Its target
      is still unidentified (see the task-2 entry and the first-print question above);
      reproducing it needs no guess about the machine, only fidelity to the G-code.
      `layer_num` is `m_layer_index` after `change_layer` increments it
      (`v2.4.2:GCode.cpp:4663`, `:4680`), so `1` is the second layer; verified by slice —
      exactly one occurrence, right after OrcaSlicer's own `M106 S127` for that layer.
- [x] **The machine-limit key is `emit_machine_limits_to_gcode`, not
      `machine_limits_usage`.** Earlier entries here and in `README.md` named
      PrusaSlicer's key. OrcaSlicer's is a bool at `v2.4.2:PrintConfig.cpp:4446`, read
      at `GCode.cpp:3939`–`3943` (`print_machine_envelope`), and it is in
      `Preset::printer_options()` (`Preset.cpp:1384`), so a user preset can set it.

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

- [x] **Ooze prevention / idle nozzle temperature — done, see Decided.** The dual
      reference drops the parked hotend to 150 °C and ramps it back (`M104 T0 S150` →
      `S168.3` → `S200`); `ooze_prevention` + `idle_temperature` now reproduce the drop.
      A second material's profile must carry its own `idle_temperature`; the reference
      never parked its PETG at all (Cura judged T1's idles too short), so 0 (= the
      process's `-5` delta) is the honest derived value for PETG until a print says
      otherwise.
- [ ] **`bed_temperature_formula`.** Defaults to `by_highest_temp`. Harmless while every
      i-Fast filament profile says 80 °C; revisit if one ever doesn't.

## WiFi upload to the i-Fast (`intent/0003`)

A separate workstream from the profile, and the only part of this file that is not about
a sliced value. Why it exists, the protocol facts, and the constraints are in
[`intent/0003`](intent/0003-wifi-upload-to-the-ifast.md); this is the live list.

**Safety rule for this whole section: never send `M6030` without asking first.** It starts
a physical print on a machine that may be unattended. `qidi_send.py` keeps it behind
`--print`, which is off by default — keep it that way.

### Before anything can be tested

- [ ] **Is the printer back on the network?** `ping -c 2 192.168.213.87`. It dropped off
      mid-session on 2026-09-09 — ICMP failing, not just UDP — and had not returned. That
      is known ChiTu WiFi-module flakiness and wants a power cycle, not debugging. Nothing
      below can move until this answers.
- [ ] **Run the read-only probe:** `python3 qidi_send.py --ip 192.168.213.87 --status`.
      Writes nothing. Should report steps/mm, geometry, firmware, temps and print
      progress. Close QIDI Print first — the module binds to one client source port and
      answers a second one with `Error:IP is connected by IP:… already!`.

### The first real upload

- [ ] **Ask before it happens** — it writes a file to the printer's storage. Small,
      obviously-named test file, and **no `--print`**. Then confirm it appears in the file
      list, on the touchscreen or via `M20`.
- [ ] **If `M28` fails, suspect storage before suspecting the script.** `M20` returned an
      empty file list, which may mean nothing was mounted. Try it with a USB drive in.
- [ ] **`M6030` has never been issued to real hardware.** Even once the upload works, the
      start-print path is unproven. Separate step, separate consent.

### Wiring it into OrcaSlicer

- [ ] **The post-processing line points at a file that does not exist.** Print Settings →
      Others → Post-processing Scripts currently reads
      `/usr/bin/python3 "/Users/brad/bin/qidi_send.py" --ip 192.168.213.87 --quiet;`
      and there is no `~/bin/qidi_send.py`. Either copy the script there or repoint Orca
      at the checkout — but decide, because the two drift otherwise.
- [ ] **Does this repo ship the uploader?** It sits at the root by placement, not
      decision. [`scripts/`](scripts/) currently means *the validation harness*, and
      neither [`README.md`](README.md) nor [`CLAUDE.md`](CLAUDE.md) §"Repo layout"
      mentions the script at all. If it ships: a home, a layout line, and a README
      section. If it does not: it should be ignored rather than tracked.
- [ ] **Reconcile the README's wording.** [`README.md`](README.md) §"Deliberately not
      configured" says the i-Fast has no network transport. That is still true *of the
      profile* — hard rule 3 is untouched, Orca has no host type for this protocol — but
      the repo now carries a tool that contradicts it at a glance. Worth a sentence.

### Unverified in the script itself

- [x] **Block framing matches the documented protocol** (verified 2026-09-09).
      `frame()` was checked against an independent reimplementation across empty,
      single-byte, 1280-byte and maximum-offset payloads: payload, then a 4-byte
      little-endian offset, then an XOR over payload-plus-offset bytes, then `0x83`.
- [ ] **Everything above the framing is mock-tested only.** `M28` / data / `M29` were
      exercised against a mock ChiTu server — 118 KB byte-identical, `resend` path fired,
      sanitisation and the WiFi-reboot retry both held — and never against the printer.
      **The mock is not in this repo**, so that result cannot be re-run; it is the
      handoff's word. If the real upload misbehaves, the mock has to be rebuilt.
- [ ] **`--compress` cannot work on this Mac and fails quietly.** The script probes
      `/Applications/QIDI Print.app/…/VC_compress_gcode_MAC` and a `QIDI-Print.app`
      variant; only `/Applications/QIDISlicer.app` is installed and no `VC_compress*`
      binary exists anywhere under `/Applications` (checked 2026-09-09). So the flag logs
      "not found" and sends plain G-code — correct behaviour, but it means the printer
      screen gets no preview and no time estimate, and the compression path is entirely
      untested. Decide whether that is acceptable or whether the binary gets sourced.
- [ ] **No bound on `resend` recovery.** A printer that keeps asking for the same offset
      loops forever. Not worth fixing before a real upload proves the path is even used.

## Unverified profile values

_Populated as profiles are written._

### From task 3 (the machine profile)

- [x] **Resolved 2026-09-20 by the first dual print: it is now `["0","0"]`, and the
      8.5 mm lives in `change_filament_gcode` instead.** The first dual print failed,
      and the retract depth turned out to be the smaller half of the problem — the
      block had no *park*, so Orca ran it standing on the part 100 times out of 100.
      Reproducing the reference's park-and-purge means owning both the retract and the
      purge, which is why this key is zeroed rather than raised to 8.5: Orca places its
      own pair on the part, at the wrong end of the travel. See **Found by the first
      dual print** below. The mechanism recorded here stays correct and is what made
      the zeroing safe to reason about.
      **Original entry, 2026-09-07 (user): leave it at 2 mm for now.** It cannot matter on a
      single-extruder print — there is no tool change — so the question is entirely about
      the first *multi-head* job. Judge it there, on stringing and ooze at the changes:
      if there are strings or blobs, set `retract_length_toolchange` to `["8.5","8.5"]`,
      which matches ground truth and is a one-key change.
      The reference retracts 8.5 mm before every tool change and primes 8.5 mm after it;
      we do 2 mm, carried from the base.
      **Correction (2026-09-07), from re-reading `v2.4.2` and measuring a real GUI dual
      slice:** the earlier claim here — that `set_extruder` calls
      `retract(toolchange=false, …)` so `retract_length_toolchange` is unreachable
      outside the wipe-tower code — **is wrong.** `GCode::set_extruder` calls
      `this->retract(true, false)` at `GCode.cpp:7753`, which routes through
      `GCodeWriter::retract_for_toolchange` and consumes **`retract_length_toolchange`
      and `retract_restart_extra_toolchange`** (`GCodeWriter.cpp:1015`–`1024`). The
      `retract(false, false, LiftType::SpiralLift, true)` at `:7956` is a *second* call,
      whose job is the lift.
      Measured in the pre-review GUI dual slice (since replaced by
      `samples/gui-2.4.2/20mm_Box_PLA_15m3s_multi.gcode`, where it is a plain 2 mm
      `G1 E-2` now that wipe is off): 1.82755 mm
      before the wipe + 0.17245 mm during it = exactly our 2 mm
      `retract_length_toolchange`, with a symmetric `G1 E2` prime after the change
      (50 of 51 changes; the initial tool selection has nothing to prime back).
      So matching the reference is a **one-key change** —
      `retract_length_toolchange: ["8.5","8.5"]` — with Orca's bookkeeping staying
      consistent, and 8.5 mm is a *derived* value, not an invention.
      Not done here because it changes what the machine physically does: 8.5 mm is a long
      retract for PLA and risks heat-creep clogs. **Hard rule 8 — ask the user.**
      Harmless to leave at 2 mm for the single-PLA first print, which has no tool change.
- [ ] **`TODO(verify):` `machine_max_acceleration_e` is 5000, QIDI publishes 10000.**
      `PrusaSlicer_fast.ini` says `machine_max_acceleration_e = 10000,5000`; the base
      chain gives `5000,5000`. Hard rule 6 (do not raise motion limits) keeps the base
      value. Every other `machine_max_*` matches the ini exactly — this is the lone
      discrepancy.
- [ ] **`TODO(verify):` `nozzle_type: ["brass","brass"]` assumes the standard head.**
      Follows the brief's "assume the standard head" instruction, not a measurement.
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
- [x] **Resolved (2026-09-07): `z_hop` is 0.** It was 0.4 with `Auto Lift`, carried
      from the base; Orca's spiral lift emitted interpolated Z values (`Z0.357143`, …) on
      every retraction, at travel speed, where QIDI Print's Z is constant across a layer.
      See **Decided: match QIDI Print's motion**. The harness's hop detector now fails
      the run if it comes back.

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
      because no QIDI i-Fast source emits `M900` and because PA is explicitly out of
      scope for this project. Two things to check after a first print: whether the Chitu
      board actually implements `M900`, and whether 0.031 is anywhere near right for
      this extruder. Turning it back on is a one-key change.
- [ ] **`TODO(verify):` `filament_flow_ratio` `0.98` is inherited and contradicts QIDI.**
      `PrusaSlicer_fast.ini` says `extrusion_multiplier = 1,1`. Both are sourced values,
      so neither is an invention; we keep the inherited 0.98 because the project scopes
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

### Found by task 5 — `M201`/`M203`/`M204`/`M205`, decided 2026-09-07

- [x] **Resolved: not emitted.** Every slice used to write `M201 X9000 Y9000 Z500 E5000`,
      `M203 X500 Y500 Z12 E120`, `M204 P1500 R1500 T1500` and
      `M205 X10.00 Y10.00 Z0.20 E2.50` before the start block, plus `M204 S500` and
      `M205 X8 Y8` from the process profile in the body. The values were the ini's, but
      QIDI Print writes none of them and the i-Fast prints on its stored limits.
      `emit_machine_limits_to_gcode: "0"` (the key an earlier version of this entry
      misnamed `machine_limits_usage`) removes the preamble; `default_acceleration` and
      `default_jerk` `0` remove the body commands. The `machine_max_*` values stay for
      the time estimate. User's decision, under **Decided**. The registry has no entry
      for any of these codes, so their return fails the harness.

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

- [x] **Resolved (2026-09-07): the 2.4.2 GUI slices two filaments fine.** The crash is
      **CLI-only**. `samples/gui-2.4.2/20mm_Box_PLA_15m3s_multi.gcode` (and the
      pre-review slice it replaced) is a real
      two-extruder 2.4.2 GUI slice of this profile: 12333 lines, 51 body tool changes,
      no abort. Whether `Preset::normalize` → `set_num_extruders` is the difference
      remains unproven (supplying those keys by hand did not stop the CLI crash), but it
      no longer blocks anything: the harness's 2.3.1 fallback is now corroborated by the
      target version. The tool-change block is confirmed on 2.4.2 — see **Found by the
      2.4.2 GUI slices** below.

#### Differences the harness reports every run, still unresolved

These are classified KNOWN: documented here, printed in full in the report, and not
failing the run. They should shrink over time.

- [ ] **`TODO(verify):` `G92 E0` after every retraction against the reference's 7.** OrcaSlicer resets
      the extruder datum after every retraction; QIDI Print's absolute `E`
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
- [x] **Resolved (2026-09-07): the spiral Z lift is gone with `z_hop` 0.** It showed
      up as `G17` + `G3` on 2.3.1 and as `G1` segments on 2.4.2. Zero `G2`/`G3`/`G17` in
      either harness output now, and the registry has no entry for them, so their
      return fails the run. The question whether the Chitu firmware accepts arcs is
      moot for this profile.

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

- [x] **Resolved 2026-09-20: `M109` now fires only when switching to T0.**
      The rewritten block uses `{if next_extruder == 0}M109 …{else}M104 …{endif}`, which
      is what the reference does. The first dual print made it urgent rather than
      theoretical — see **Found by the first dual print** below. Original entry:
      `change_filament_gcode` is variant C's shape, so every switch waits for
      temperature. The reference blocks on `M109 S200` when switching **to T0** (variant
      C, 24×) but not on later switches to T1 (variant B, which relies on T1 already
      being hot). Ours therefore emits 103 `M109` against the reference's 27. One string
      cannot be both, and task 3 chose the safe one deliberately — but it costs a
      temperature wait on every change, which will slow a dual print. Revisit if the
      first dual print is unacceptably slow.
- [ ] **`TODO(verify):` OrcaSlicer's preheat/cooldown schedule differs from Cura's.**
      Ours, with ooze prevention on: `M104 S<idle> T<old> ;cooldown` before the `T`
      when the tool will idle longer than `preheat_time`, else `; removed M104`;
      `M104 S<t> T<n> ; preheat T<n> time: 30s` backtraced 30 s ahead; and Orca's own
      `M109 S<t> T<n>` wait after the change on top of ours. The reference: a bare
      `M104 T0 S200` about 107 lines ahead with interpolated intermediate setpoints,
      and T0 parked at 150 on every one of its 27 long idles; the PETG on T1 never
      parked. Same idea, different model; the commands the firmware sees are the same.
      Watch the first dual print for tool changes that wait noticeably on `M109`.

### Found by the 2.4.2 GUI slices (2026-09-07)

Two G-code files sliced by hand in the OrcaSlicer 2.4.2 GUI from the reference's own
20 mm box — one extruder, and two extruders with our PLA in both slots. Kept in
[`samples/gui-2.4.2/`](samples/gui-2.4.2/README.md), because the harness cannot produce
them: it drives the CLI, and the CLI cannot slice two filaments on 2.4.2 at all.

Confirmed, and previously unproven:

- [x] **All three presets load and resolve in the GUI, no substitution.** The embedded
      `; CONFIG_BLOCK` names `QIDI i-Fast 0.4 nozzle`, `0.20mm Standard @QIDI i-Fast` and
      `QIDI Generic PLA @QIDI i-Fast` (both slots), with `printable_area`
      `0x0,330x0,330x250,0x250`, `printable_height 320`, `nozzle_diameter 0.4,0.4`,
      `single_extruder_multi_material 0`, `use_relative_e_distances 0`,
      `initial_layer_print_height 0.3`, `enable_prime_tower 0`, `disable_m73 1`,
      `support_air_filtration 0`, `manual_filament_change 0` and
      `machine_max_acceleration_e 5000,5000,5000,5000`. Every one of those arrives
      through `inherits`, which the CLI never resolves — so this is the first proof the
      thin presets are correct as written, not just as flattened.
- [x] **`curr_bed_type = High Temp Plate` in the GUI.** Exactly as predicted: the GUI
      honours `default_bed_type: "3"` where the CLI falls back to Cool Plate. Both paths
      now emit `M140 S80` / `M190 S80` — the CLI only because the filament profile sets
      all twelve plate-temp keys.
- [x] **The tool-change block is confirmed on the target version.** 51 body tool changes,
      every one `T<n>` / `G92 E0` / `M109 S200` — our `change_filament_gcode` verbatim —
      26 to T0, 25 to T1, each preceded by Orca's retract + wipe + `G92 E0` and followed
      by a `G1 E2` prime. Task 6 could only show this on 2.3.1.
- [x] **The `is_extruder_used[1]` conditional works in the GUI, in both directions.**
      Single file: `T1` heating pair commented out, prime line `B0`. Dual file: pair
      live, prime line `B19`. That is what `single-extruder.gcode` and
      `dual-extruder.gcode` do respectively. The start block is otherwise identical to
      the reference in both, and **the end block is byte-identical in both.**
- [x] **Zero `M900`, `M106 P<n>`, `M73`, `;TIMELAPSE_TAKE_FRAME`, `;BEFORE_LAYER_CHANGE`
      or `M83` in either file**, and the first layer is at `Z0.3`. The four
      machine-profile keys that suppress those are doing their job in the GUI too.
- [x] **`;_FORCE_RESUME_FAN_SPEED` survives only after the *initial* tool selection.**
      One occurrence per file, on 2.3.1 and 2.4.2 alike; for every later change the
      post-processor replaces the marker with the real `M106`. `README.md` had shown it
      as if it followed every tool change — corrected.

New difference, not previously seen:

- [ ] **`TODO(verify):` the single-extruder GUI slice emits a bare `T0` the reference and
      the CLI do not.** It sits right after OrcaSlicer's `G90` / `G21` / `M82` preamble,
      framed by `G92 E0`, before the first layer:

      ```gcode
      M82 ; use absolute distances for extrusion
      G92 E0
      T0            <- this
      G92 E0
      M106 S0
      ```

      Mechanism is clear: with one filament in use `m_writer.multiple_extruders` is
      false, so `GCode::set_extruder` takes the early return at
      `v2.4.2:GCode.cpp:7717`–`7747` and emits nothing but `m_writer.toolchange(0)` —
      no `change_filament_gcode`, hence no `M109` after it. The CLI slice of the same
      profile emits no `T0` there at all, so **the harness is blind to this line.**
      Why the CLI differs — established 2026-09-07: `GCodeWriter::toolchange`
      (`v2.4.2:GCodeWriter.cpp:576`) writes the `T` only when `multiple_extruders` is
      true *or* `filament_diameter` has more than one entry. The GUI always carries two
      filament slots on a two-extruder printer; the CLI single case loads one filament.
      So the line is unavoidable in the GUI and cannot be reproduced from the CLI.
      Impact is probably nil — T0 is already the active tool, the start block having
      selected it — but the i-Fast's head auto-lift is firmware behaviour triggered by
      tool changes, so a redundant `T0` is worth one look on the first print: watch
      whether the head does a lift/park cycle between the prime line and the first layer.
      Do **not** try to suppress it by editing the start block; it is emitted after the
      start block, by OrcaSlicer, not by us.

Not a defect, worth stating: the dual file's tool-change **count** (51) and surface
assignment differ from the reference's (49) because the user assigned extruders to
different surfaces. That is a property of the job, not the profile — the same caveat the
harness's own dual fixture carries.

Both files were **re-sliced after the first-print review** (same day) and now show the
review's motion and ooze-prevention output from the GUI side; everything above still
holds for the new pair (single: `20mm_Box_PLA_12m3s.gcode`, dual:
`20mm_Box_PLA_15m3s_multi.gcode`).

### Found by task 7 (packaging)

Packaging changed no profile value. It checked four things and added two files.

- [x] **Every key in `profiles/machine/` is now documented in `README.md`.** Auditing the
      shipped machine profile against the flattened base found no undocumented *value* —
      but six groups of keys had no provenance line: `manual_filament_change`,
      `nozzle_type`, `printer_notes`, `printer_variant`, the two `default_*_profile`
      forward references, and the fourteen per-extruder arrays
      (`retraction_*`, `z_hop*`, `wipe*`, `max/min_layer_height`, `extruder_colour`).
      All are base values or already-decided items; they are now in the table.
- [x] **The per-extruder arrays are base values, extended to length 2, and that is why
      they are in the file at all.** In the GUI Orca extends them itself:
      `Preset::normalize` → `set_num_extruders` (`v2.4.2:PrintConfig.cpp:8829`) resizes
      every per-extruder vector by duplicating `values.front()` (`Config.hpp:661`). The
      CLI never calls `normalize`, so the explicit length-2 arrays are what make a
      command-line slice see two extruders configured as the GUI would configure them.
      No value differs from the base.
- [x] **`manual_filament_change: "0"` is OrcaSlicer's own default, restated.** Worth
      keeping explicit because the failure is silent and total: with it enabled Orca
      skips `change_filament_gcode` at the first tool change and turns every `T` into a
      comment for the whole print (`GCode.cpp:7959`–`7960`;
      `GCodeWriter::toolchange_prefix`, `GCodeWriter.cpp:547`–`551`).
- [x] **The installed copy matches the repo.** All seven files under
      `~/.var/app/com.orcaslicer.OrcaSlicer/config/OrcaSlicer/user/default/` are
      byte-identical to `profiles/` (2026-09-07), so the install procedure in
      `README.md` is the one that was actually exercised.
- [x] **`scripts/validate.sh` re-run at package time: 0 unexpected in both cases**
      (single 10 accepted / 10 known; dual 90 accepted / 38 known).
- [x] **`LICENSE` and `NOTICE` added.** `LICENSE` is a verbatim copy of OrcaSlicer
      `v2.4.2`'s `LICENSE.txt` — the unmodified GNU AGPL v3 text, 661 lines, SHA-1
      `78e50e186b04c8fe1defaa098f1c192181b3d837`, identical to the source file. `NOTICE`
      carries the Slic3r → PrusaSlicer → Bambu Studio → OrcaSlicer → here chain, the
      per-file derivation (which preset each JSON inherits), the fact that `reference/`
      is QIDI's own output rather than ours, and a no-affiliation statement. JSON has no
      comment syntax, so in-file attribution lives in the machine profile's
      `printer_notes`, which already names the base preset, the licence and the sources.

### Found by the first dual print (2026-09-20)

Three prints on 2026-09-12 — one head, both heads, the other head. The single-head jobs
printed; the two-head job stuck for a few layers, went spongey and came off the plate.
G-code and photos are **local working files and are not committed** — filenames below
are pointers for whoever has them, not paths in this repo. Written up in
[`intent/0004`](intent/0004-make-the-dual-extruder-print-work.md).

#### Ruled out: the heads do lower after a tool change

- [x] **The firmware head lift is fine.** The starting hypothesis was that a head was not
      dropping all the way back after a `T`. Three things say otherwise. Every one of the
      100 body tool changes is followed by an absolute `G1 Z<layer> F300` before the next
      extrusion, so the slicer always re-commands Z. `CUBE-head2.gcode` performs a real
      `T0`→`T1` change after its start block and printed correctly. And the **control
      print settled it**: `reference/dual-extruder.gcode`, QIDI Print's own dual file,
      printed unmodified and came off the plate intact (2026-09-20,
      `PXL_20260920_213350134.jpg`, local). Hard rule 4 stands — nothing here
      touches the lift.

#### Fixed

- [x] **The tool change ran standing on the part, 100 times out of 100.** OrcaSlicer runs
      a custom `change_filament_gcode` wherever the previous extrusion ended. Measured by
      script over `CUBEx2-multi.gcode`: every `T` line executed with the head inside an
      object footprint (X 155–175, Y 104–124 or 126–146) at print Z. With `z_hop = 0`,
      `wipe = 0` and `reduce_crossing_wall = 0`, the incoming nozzle then arrived drooled
      and de-pressurised and got 2 mm of prime at the start of the next wall — the strands
      radiating across the whole plate in `PXL_20260912_170507605.jpg` (local) are
      that, every layer, for 100 layers. QIDI Print
      parks at the bed edge and dumps 8.5 mm of purge there instead — 24 parks at `X330`,
      25 at `X0.00`, 49 staged returns through `X165 Y89.6`. Fixed by rewriting the block;
      see `README.md` §*Park and purge*.
- [x] **Ooze prevention was waiting twice per tool change.** `OozePrevention::post_toolchange`
      emits its own blocking `M109 S<t> T<n>` on top of the one in `change_filament_gcode`.
      The failing print reached 5 % in 15 minutes (`PXL_20260912_161351797.jpg`, local) against
      OrcaSlicer's own `43m 49s` estimate for the whole job, and the 15 cooldowns that
      survived the 30 s backtrace all fell in the slow early layers — where the part
      stopped sticking. `ooze_prevention` is now `"0"` in all five process profiles.
      `idle_temperature: ["150"]` stays in the filament profile but is now inert.
- [x] **A parenthesis bug that would have refused to slice.** `{x == 0 ? a : b}` does not
      parse — *"Parsing error. Expecting tag alternative"*, caret on the `==`. The working
      form is `{(x == 0) ? a : b}`. `{if x == 0}…{else}…{endif}` needs no parentheses.
      Verified against 2.4.2 by probing all four forms through `machine_start_gcode`.
      Worth remembering: the repo's only prior ternary (`{is_extruder_used[1] ? 19 : 0}`)
      is a bare boolean and never exercised this.

#### Still open

- [ ] **`TODO(verify):` the park sweeps X at whatever Y the head is on.** The reference
      parks at `X330 Y89.6` / `X0.00 Y89.6`, but that `Y` is Cura-computed from one
      object and would be an invented constant here — and an unsafe one, 89.6 mm into a
      250 mm bed. Ours moves in X only. **Limitation: an object sitting at higher X in
      the same Y band as the part being left would be crossed by the sweep**, at print Z
      with no hop. Fine for anything centred on the plate; needs a real multi-object
      layout to prove out. If it bites, the fix is a staged return like the reference's
      (`G0 X165 Y<clear>` at the end of the block) with a `Y` taken from the machine, not
      from Cura.
- [ ] **The rewritten block has not been executed by a slicer.** It parses and expands
      correctly — verified by probing it through `machine_start_gcode` on 2.4.2, which
      produced exactly the intended nine lines — but no *tool change* has run it. The
      2.4.2 CLI cannot slice two filaments (see below; it segfaults on macOS too, rc 139,
      which corroborates the upstream bug on a second platform) and no 2.3.1 fallback
      exists on this machine. **Needs a 2.4.2 GUI slice of the two-cube job**, checked for:
      every `T` at `X0` or `X330` and none inside an object footprint; `G1 F1200 E8.5`
      immediately after each `T`; `M109` only on switches to T0.
- [ ] **Stringing to the left and right plate edges is expected, and unquantified.** The
      control print did it too — the strands run to `X0` and `X330`, the two parks. QIDI's
      return leg is un-retracted; ours should be better, because the 8.5 mm retract
      precedes the park move and Orca's own travel retract covers the return. Nobody has
      compared the two yet. Discount the control's severity for T1 running at 230 °C, the
      reference's PETG temperature, with PLA loaded.
- [ ] **The standby drop is gone with `ooze_prevention` off.** The reference has it and
      the control print used it successfully. If the idle nozzle oozes now that a purge
      exists, the way back is *not* this flag but the reference's own line —
      `M104 S150 T{previous_extruder}` before the `T`, inside `change_filament_gcode` —
      which buys the standby without a second blocking wait.

#### The two heads are not aligned in XY — and it is not ours

- [ ] **The nozzle offset needs calibrating on the machine.** In the control print's
      close-up (`PXL_20260920_213836060.jpg`, local) the two materials' nested walls
      are not concentric: the band is wide on one side and pinched to nothing on the
      opposite side. The reference model nests them 0.4 mm apart (T0's outer wall spans
      X155.2–174.8, T1's inner walls 156.4–173.6, 156–174, 155.6–174.4), so a uniform
      band is what correct alignment looks like — and the band vanishing on one side puts
      the error at ≥ 0.4 mm on that axis. Half of widest-minus-narrowest gives the
      magnitude.
      **That part came off QIDI Print's own G-code**, with no OrcaSlicer profile involved,
      so this is pre-existing and was silently degrading the failed print too.
      **No profile key changes**: hard rule 5 keeps `extruder_offset` at `["0x0","0x0"]`
      because the i-Fast applies offsets in firmware and a slicer value would double-apply
      (QIDI's own `PrusaSlicer_fast.ini` agrees: `extruder_offset = 0x0,0x0`). The action
      is the machine's own XY offset calibration, then re-print the control file and check
      the band is even. Log the measured offset here when it is known.

#### The harness runs on macOS now, with overrides

- [ ] **`scripts/validate.sh` defaults to the Linux flatpak; this repo is on macOS.**
      It runs with:
      `ORCA_CMD="/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer"` and
      `ORCA_SYSTEM_DIR="$HOME/Library/Application Support/OrcaSlicer/system/Qidi"`.
      The single-extruder case passes unchanged — **10 accepted, 6 known, 0 unexpected**.
      The dual case is **BLOCKED**: `ORCA_DUAL_CMD` points at a Linux AppImage that does
      not exist here, so the run exits non-zero on a blocked check rather than on a real
      difference. Either build a macOS fallback slicer or make the dual case's evidence a
      GUI sample; until then the harness cannot see the tool-change block at all on this
      machine. `CLAUDE.md` §Environment still describes the Linux box.

### Found by the first-print review (2026-09-07)

A review of what the sliced *body* asks the machine to do, against the reference and
against QIDI's Cura definition (`CURA/qidi.zip` in QIDI's published bundle, not mined
before — see [`reference/qidi-profiles.md`](reference/qidi-profiles.md)). The decisions
are under **Decided**; what is still unverified:

- [ ] **`TODO(verify):` `travel_speed` 100 — the ini says 130.** Two QIDI sources
      disagree: the reference G-code (and the Cura definition that produced it) says
      100 mm/s, `PrusaSlicer_fast.ini` says `travel_speed = 130`. G-code wins by rule;
      130 is also sourced and safe to try if 100 feels slow. Either is a fraction of the
      500 the base asked for.
- [ ] **`TODO(verify):` retraction 1.5 mm @ 30 mm/s, no wipe — the ini says 2 mm @ 40.**
      Same shape of disagreement: reference G-code and Cura say 1.5 @ `F1800` with no
      wipe; the ini says `retract_length = 2`, `retract_speed = 40`, `wipe = 0`. Both
      are QIDI's numbers. Neither is a calibration; the first print is.
- [ ] **`TODO(verify):` `retraction_minimum_travel` 2 and `retract_when_changing_layer`
      1 are the base's.** Cura says `retraction_min_travel 1.5`; the ini says
      `retract_layer_change = 0`. Left at the base values (the ini agrees on 2 for the
      first; a layer-change retract is harmless). Recorded so nobody thinks they were
      checked.
- [ ] **`TODO(verify):` `travel_speed_z` 5 reaches only OrcaSlicer's Z-only moves.**
      Layer changes are folded into the layer's first XY travel (`G1 X Y Z F6000`), as
      Cura does at `F300`; the Z component of such a move is tiny, so the firmware's
      Z limit is what matters and QIDI Print relies on the same thing (its start block
      moves Z 50 mm at `F3600`). The key does govern the descent to the first layer and,
      on 2.3.1, the unlift at every tool change — both now `F300`.
- [ ] **`TODO(verify):` OrcaSlicer parks *both* tools; QIDI Print parked only T0.**
      With `ooze_prevention` on, whichever tool leaves gets the cooldown (unless it
      returns within `preheat_time`). Cura only cooled a tool whose idle was long
      enough, which in the reference job meant T0 and never the PETG on T1. On a job
      where the tools alternate quickly this means more heat cycles than QIDI Print
      would issue, never a hot oozing idle nozzle. Judge on the first dual print.
- [ ] **`TODO(verify):` `M106 T-2 S255` lands one line later than in the reference.**
      QIDI Print emits it just before `;LAYER:1` and before that layer's fan command;
      OrcaSlicer's `layer_change_gcode` runs after its own `M106 S127` for the layer.
      Same two commands, swapped; no reason to expect the firmware to care.

Not unverified, but found and worth keeping:

- [x] **The tool-change block does not under-prime.** Measured on the 2.4.2 GUI dual
      slice, the 2.3.1 harness dual slice and the reference: the incoming extruder has
      exactly 0 mm retract debt at its first printing move after every one of the
      51 / 101 / 49 tool changes. Now a standing harness check (**Tool-change priming**)
      with no registry entry, so it can never be accepted away.
- [x] **Per-feature printing speeds already matched the reference** — walls 30, infill
      60, first layer 20 mm/s — through inheritance. Only travel was wrong.
- [x] **The harness gained two checks** (motion envelope, tool-change priming) and a
      canonical form for temperature commands, and *lost* two registry entries
      (`machine-limit-mcodes`, `spiral-z-lift`) so that those subjects fail the run if
      they reappear. Verified: restoring `z_hop` 0.4 and `default_jerk` 8 fails with the
      hop detector at 12.46 and `M205` in the census.

### Found by preparing for publication (2026-09-08)

Publishing the repo as `OrcaSlicer-QIDI-i-Fast`. No profile value changed except one
comment string.

- [x] **QIDI's published profile bundle is no longer in the repo.** All 28 files under
      `reference/qidi-profiles/` were QIDI Technology's own distribution, redistributed
      here — 38.5 MB, 95 % of the repository, and not ours to host.
      [`reference/qidi-profiles.md`](reference/qidi-profiles.md) replaces it with the
      download location, a SHA-256 manifest of exactly what these notes were written
      against, and the three files the provenance actually depends on
      (`prusaslicer/PrusaSlicer_fast.ini`, and `qidi.def.json` / `i-fast.def.json` inside
      `CURA/qidi.zip`). The directory is now git-ignored, so a re-download for local work
      cannot be committed back. Every claim in `README.md` remains checkable; it just
      costs a download first.
- [x] **`ifast-orca-profile-handoff.md` is gone**, folded into
      [`intent/0001`](intent/0001-orcaslicer-profile-for-the-ifast.md) (objective, inputs,
      the seven tasks) and `CLAUDE.md` (hard rules, definition of done), which is now
      authoritative for both. It predated the `intent/` convention and fused intent with
      design; the doc-roles table in `CLAUDE.md` no longer lists it.
- [ ] **`TODO(verify):` a `.orca_printer` bundle would not import as-is.** The release
      artifact is a plain zip matching the documented copy-in-place install, because
      Orca's one-click import path will not take our presets unmodified.
      `PresetBundle::import_json_presets` (`v2.4.2:PresetBundle.cpp:1450`+) routes each
      file by whether the config **it alone** carries `printer_settings_id`,
      `print_settings_id` or `filament_settings_id`, *before* `inherits` is applied — and
      all seven of ours omit those keys, inheriting them instead. A bundle built straight
      from `profiles/` would therefore import **nothing**, logging only
      `Preset type is unknown, not loading`. Orca sets the key to the preset's own name
      when it saves a user preset (`Preset.cpp:2780`), so injecting it at package time is
      derivable rather than invented — but it cannot be confirmed without a GUI import,
      which the harness cannot do. Worth its own intent before anyone builds it.
- [x] **The GUI samples now differ from the profile by one comment string.** The machine
      profile's `printer_notes` was reworded when the bundle stopped being redistributed,
      and both files in `samples/gui-2.4.2/` embed the old wording in their
      `; CONFIG_BLOCK`. Nothing sliced changed. Recorded in
      [`samples/gui-2.4.2/README.md`](samples/gui-2.4.2/README.md); they are re-sliced at
      the next GUI session, which the first print needs anyway.

### From task 2 (the reference G-code extraction)

- [ ] **`TODO(verify):` `M106 T-2 S255` / `M107 T-2` — which fan is `T-2`?** `-2` is not a
      valid extruder index. Both occurrences sit at a `;TIME_ELAPSED` boundary (end of
      layer 0, and the shutdown block), so it is not a per-tool part-cooling fan.
      Candidates are the chamber circulation fan and the auxiliary/side fan. QIDI's Cura
      definitions do not mention it; the QIDI Print engine adds it. **Do not guess** —
      the user has the machine. Since 2026-09-07 the profile *reproduces* both commands
      (see **Decided**), so the question no longer changes what the machine does, only
      what we know about it; the first print answers it.
- [ ] **`TODO(verify):` `M4010` payload encoding.** `M4010 X<w> Y<h>` followed by
      `M4010 I<offset> T<length> '<hex>'` chunks — a preview bitmap for the display
      (186×186 single, 304×304 dual). Undocumented. Orca cannot emit it. Cosmetic, but
      confirm the printer does not sulk without a preview.
- [ ] **`TODO(verify):` does `M2100 T<seconds>` matter?** Print-time estimate handed to
      the display; matches the `;TIME:` comment exactly. Orca has no equivalent. Confirm
      whether the i-Fast's "time remaining" readout misbehaves without it.
- [ ] **`TODO(verify):` `preheat_time` vs Cura's ramp.** The reference preheats the parked
      hotend ~107 lines before the tool change (`M104 T0 S200`), with interpolated
      intermediate setpoints (`S168.3`, `S155.4`). Orca's `preheat_time` (30 s) is a
      different model and will not reproduce those values. Now live, since ooze
      prevention is on; the harness classifies the ramp values as an accepted Cura
      artifact and the schedule difference as known. See the task-6 entry above.
- [ ] **`TODO(verify):` chamber heater is never used.** Both references emit only
      `M141 S0` and no `M191`. The i-Fast has an actively heated chamber; QIDI Print
      simply does not drive it in these exports. Out of scope per the brief, noted so
      nobody reads `M141 S0` as "the machine has no chamber heater".

### Found by the WiFi work (2026-09-09)

- [ ] **`TODO(verify):` the printer reports a build volume this repo does not.** The
      `M4001` handshake came back `ok X:0.010611 Y:0.010611 Z:0.002500 E:0.007300
      T:0/372/250/321/2 U:'UTF-8' B:1`, whose `T:` field parses as machine type `0` then
      **372 / 250 / 321**. The profile ships `printable_area` `0x0, 330x0, 330x250, 0x250`
      and `printable_height` `320`, both taken from QIDI's own
      `PrusaSlicer_fast.ini` (`bed_shape`, `max_print_height` — see
      [`README.md`](README.md)). Y agrees; **X is 42 mm wider and Z 1 mm taller** in what
      the firmware reports.
      The benign reading is that firmware reports axis travel, not printable area — a
      dual-extruder machine needs X travel beyond the plate so the idle head can park off
      it, and 42 mm is about a carriage spacing. The alarming reading is that the ini
      understates the real bed. **Do not widen the profile on the strength of this** —
      that would be inventing a value against two published sources, and hard rule 1
      forbids it. What settles it: measure the plate, or watch where the head can travel.
      Recorded because `intent/0003` surfaced it and nothing else in the repo would have.

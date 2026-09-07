# Ground truth extracted from the QIDI Print reference G-code

Task 2 of [`../ifast-orca-profile-handoff.md`](../ifast-orca-profile-handoff.md).

This file is the **authority** on how the QIDI i-Fast is driven. Where it disagrees with a
summary elsewhere in the repo, this file wins — it is transcribed directly from the two
reference exports and every block below is reproducible with the `sed` command quoted
beside it.

The reference G-code itself is **read-only**. `.gitattributes` marks `reference/**` as
`-text -diff` so Git cannot rewrite its CRLF line endings; `core.autocrlf=input` is set on
this machine and would otherwise normalise them.

---

## 1. Provenance

| | `single-extruder.gcode` | `dual-extruder.gcode` |
|---|---|---|
| Exported by | `Cura_SteamEngine 4.9.1` | `Cura_SteamEngine 4.9.1` |
| Flavor | `;FLAVOR:Marlin` | `;FLAVOR:Marlin` |
| Cura definition | `i-fast` | `i-fast` |
| Line endings | CRLF | CRLF |
| Total lines | 3628 | 11411 |
| `M4010` thumbnail block | lines 1–131 | lines 1–458 |
| G-code header begins | line 132 | line 459 |
| Materials | PLA on T0 | PLA on T0, PETG on T1 |
| Print time | `;TIME:861` | `;TIME:2607` |
| Tool changes | 0 in the body | 49 in the body |
| Trailing `;SETTING_3` blob | absent | lines 11401–11411 |

Both files quote `sha1sum` values that must not change:

```
352aca886b8d844fcebc2f49aee09f38978fb04c  reference/single-extruder.gcode
0e2ab6397396dcab47bc8420ec173c9919030f91  reference/dual-extruder.gcode
```

The line numbers below refer to the **raw** files, CRLF included. All excerpts are shown
with the `\r` stripped for readability; nothing else has been altered.

---

## 2. Start block, verbatim

`sed -n '132,164p' reference/single-extruder.gcode`

```gcode
;FLAVOR:Marlin
;TIME:861
;Filament used: 0.825944m, 0m
;Layer height: 0.2
;MINX:150
;MINY:110
;MINZ:0.3
;MAXX:180
;MAXY:140
;MAXZ:9.9
M2100 T861
;Generated with Cura_SteamEngine 4.9.1
;T0
M82 ;absolute extrusion mode
G92 A0 B0
G28
G1 X0 Y0 Z50 F3600
M140 S80
M104 T0 S200
;M104 T1 S230
M190 S80
;M109 T1 S230
M109 T0 S200
G92 E0
G92 A0 B0
G0 X0 Y4 Z0.3 F3600
T1
G1 X330 B0 F2400
T0
G1 X330 Y5 F3600
G1 X5 A19 F2400
G92 A0 B0
G0 X5 F2400
```

`sed -n '459,491p' reference/dual-extruder.gcode`

```gcode
;FLAVOR:Marlin
;TIME:2607
;Filament used: 0.491199m, 1.47706m
;Layer height: 0.2
;MINX:0
;MINY:89.6
;MINZ:0.3
;MAXX:330
;MAXY:145.8
;MAXZ:9.9
M2100 T2607
;Generated with Cura_SteamEngine 4.9.1
;T0
M82 ;absolute extrusion mode
G92 A0 B0
G28
G1 X0 Y0 Z50 F3600
M140 S80
M104 T0 S200
M104 T1 S230
M190 S80
M109 T1 S230
M109 T0 S200
G92 E0
G92 A0 B0
G0 X0 Y4 Z0.3 F3600
T1
G1 X330 B19 F2400
T0
G1 X330 Y5 F3600
G1 X5 A19 F2400
G92 A0 B0
G0 X5 F2400
```

The two blocks differ in exactly **three** places, and every one of them is a
consequence of whether T1 carries filament in this job:

1. `;M104 T1 S230` / `;M109 T1 S230` are **commented out** in the single file. QIDI Print
   emits the lines either way and comments them when the tool is unused.
2. The T1 prime extrudes `B19` in the dual file and `B0` in the single file.
3. `;Filament used:` reports `0m` for the second extruder in the single file.

Everything else — homing, the `Z50` lift, the heating order, the `A19` prime for T0 — is
byte-identical between the two exports.

### The `;Print in advance` preamble

Immediately after the start block, both files emit the same eleven lines. Only the purge
line's coordinates and E value differ.

`sed -n '165,175p' reference/single-extruder.gcode`

```gcode

M141 S0
G92 E0
;G92 E0
;G1 F1800 E-1.5
;LAYER_COUNT:49
;Print in advance
G1 F1800 E0
G1 F2400 X151.017 Y111.999 E11.73037
G92 E0

```

The dual file is the same with `X147.594 Y108.322 E11.41078`
(`sed -n '492,502p' reference/dual-extruder.gcode`).

Two things worth noting:

- **`M141 S0` sits here, after the prime — not in the heating order.** The chamber heater
  is explicitly set to off at the start of every job in both references.
- The blank lines are real. Line 165 and line 175 are empty in the source.

---

## 3. The `A` / `B` prime line

`A` is extruder 0's own extrusion axis and `B` is extruder 1's. Addressing them directly is
how QIDI Print primes **both** hotends without paying for a tool change: it moves to `X330`
extruding on `B`, switches to T0, then moves back to `X5` extruding on `A`.

All five occurrences in each file, and there are no others:

```
single: 146  G92 A0 B0
        156  G92 A0 B0
        159  G1 X330 B0 F2400
        162  G1 X5 A19 F2400
        163  G92 A0 B0

dual:   473  G92 A0 B0
        483  G92 A0 B0
        486  G1 X330 B19 F2400
        489  G1 X5 A19 F2400
        490  G92 A0 B0
```

Reproduce with `grep -nE '(^| )[AB][-0-9]' reference/*.gcode`.

The **print body never uses `A` or `B`** — 1855 absolute `E` moves in the single file,
7802 in the dual, and the tool change uses plain `E` as well. So the axes are confined to
the start block and need no support anywhere else.

> **Correction.** An earlier note in `CLAUDE.md` recorded the prime line as
> `G1 X330 B19 F2400` unconditionally and concluded that pasting the start block verbatim
> "needs no special handling". That is only true for the dual case. The `B` value is
> `19` when T1 is used and `0` when it is not, so a single hardcoded start block will
> either purge 19 mm out of an unloaded second hotend or fail to prime a loaded one.
> This is a decision task 3 has to make; see §7.

---

## 4. End block, verbatim

`sed -n '3613,3628p' reference/single-extruder.gcode`

```gcode
;TIME_ELAPSED:861.259269
G1 F1800 E824.44436
M107 T-2
M140 S0
M107
M104 S0 T0
M104 S0 T1
M140 S0
;Retract the filament
G92 E1
G1 E-1 F300 Z320
G0 F3600 X320 Y0
M84
M82 ;absolute extrusion mode
M104 S0
;End of Gcode
```

The dual file's end block is at `sed -n '11385,11400p' reference/dual-extruder.gcode` and
is **byte-identical from `M107 T-2` onward**:

```
$ diff <(sed -n '3615,3628p' reference/single-extruder.gcode) \
       <(sed -n '11387,11400p' reference/dual-extruder.gcode)
(no output)
```

Only the preceding `G1 F1800 E<n>` final retract differs (`E824.44436` vs `E53.10365`),
which is a coordinate.

Notes on the block as written:

- `M140 S0` is emitted **twice**, before and after the two `M104 S0 T<n>`. Redundant, but
  this is what the machine is fed, so it is carried verbatim.
- `M107` also appears twice, once as `M107 T-2` and once bare.
- `G92 E1` immediately before `G1 E-1 F300 Z320` makes the retract a 2 mm move in absolute
  mode, combined with a Z lift to the full `320` build height.
- The park is `X320 Y0` — front-right, inside the 330 × 250 envelope.
- The trailing `M82` and `M104 S0` are emitted after `M84` disables the motors.

The dual file then adds the Cura `;SETTING_3` blob (lines 11401–11411), an embedded copy of
the quality profile. It is not machine-directed and has no Orca equivalent.

---

## 5. Heating and chamber

Ordering in the start block, dual file (single is the same with the T1 lines commented):

```gcode
M140 S80          ; set bed, do not wait
M104 T0 S200      ; set T0 nozzle, do not wait
M104 T1 S230      ; set T1 nozzle, do not wait
M190 S80          ; wait for bed
M109 T1 S230      ; wait for T1
M109 T0 S200      ; wait for T0
```

Everything is *set* first and *waited on* afterwards, so the bed and both nozzles heat in
parallel. The bed is waited on before the nozzles.

**Bed temperature is 80 °C in both files**, and it is never changed mid-print — the only
other bed commands in either file are the two `M140 S0` in the shutdown block. Adding PETG
on T1 did not move it. So 80 °C is what QIDI Print asks for on this machine regardless of
material, not a PLA-specific number.

This contradicts `reference/qidi-profiles/prusaslicer/PrusaSlicer_fast.ini`, which says
60 °C. The G-code is ground truth; 80 °C wins. The discrepancy is recorded in `README.md`.

**Chamber:** the only chamber command in either file is a single `M141 S0` — see §2. There
is no `M191` (wait-for-chamber) anywhere. The i-Fast has an actively heated chamber, but
QIDI Print does not use it in these exports.

---

## 6. M-code and G-code glossary

Counts are from `grep -o '^M[0-9]*' <file> | sort | uniq -c`.

### Standard Marlin codes

| Code | single | dual | Observed forms | Meaning |
|---|---|---|---|---|
| `G0` | 1246 | 2326 | — | Travel move |
| `G1` | 1855 | 7802 | — | Extrusion / feed move |
| `G28` | 1 | 1 | bare | Home all axes; start block only |
| `G92` | 7 | 105 | `E0`, `E1`, `A0 B0` | Set position |
| `M82` | 2 | 2 | `M82 ;absolute extrusion mode` | **Absolute** extruder mode |
| `M84` | 1 | 1 | bare | Disable steppers |
| `M104` | 5 | 80 | see below | Set nozzle temp, do not wait |
| `M106` | 3 | 51 | `S63.8` `S127.5` `S255` `T-2 S255` | Fan on |
| `M107` | 3 | 3 | bare, `T-2` | Fan off |
| `M109` | 1 | 27 | see below | Set nozzle temp and wait |
| `M140` | 3 | 3 | `S80` ×1, `S0` ×2 | Set bed temp, do not wait |
| `M190` | 1 | 1 | `S80` | Set bed temp and wait |

`M104` argument forms in the dual file:

```
 27×  M104 T0 S150      standby: park T0 while T1 prints
 25×  M104 T0 S200      preheat T0 back to print temp, issued mid-print
 20×  M104 T0 S168.3    interpolated ramp on the parked T0
  2×  M104 T1 S230      start block + layer 0
  1×  M104 T0 S155.4    ramp, near the end of the print
  1×  M104 T0 S0        final tool change: T0 is done, switch it off
  1×  M104 S200         end of layer 0, no tool argument
  1×  M104 S0 T0        shutdown
  1×  M104 S0 T1        shutdown
  1×  M104 S0           shutdown, trailing
```

`M109`: `M109 S200` ×24, `M109 S230` ×1, `M109 T0 S200` ×1, `M109 T1 S230` ×1.
The `T`-less forms are all inside tool-change blocks and address the tool just selected.

Note the argument order is **not** consistent: the start block writes `M104 T0 S200`
(tool first) and the shutdown block writes `M104 S0 T0` (tool last). Both are reproduced
verbatim rather than normalised.

### QIDI-specific and unexplained codes

| Code | Occurrences | What is known | Status |
|---|---|---|---|
| `M4010` | 131 single / 458 dual | Thumbnail / preview blob. First line is `M4010 X186 Y186` (single) or `M4010 X304 Y304` (dual) — a preview resolution. Subsequent lines are `M4010 I<offset> T<length> '<hex payload>'`, a chunked bitmap. | `TODO(verify):` payload encoding is undocumented. Cosmetic only — the printer displays a preview. Orca cannot emit this. |
| `M2100 T<seconds>` | 1 each | Print time estimate handed to the display. `T861` / `T2607` match the `;TIME:` comment exactly. | `TODO(verify):` whether the i-Fast's display or its "time remaining" readout misbehaves without it. |
| `M141 S<n>` | 1 each | Chamber heater setpoint. Both references emit `M141 S0`. | Understood. |
| `M106 T-2 S255`, `M107 T-2` | 1 each per file | `T-2` is not a valid extruder index. Both appear at the `;TIME_ELAPSED` boundary — `M106 T-2 S255` at the end of layer 0 and `M107 T-2` in the shutdown block — so it addresses a fan that is not a per-tool part cooling fan. | `TODO(verify):` **do not guess which fan.** Candidates are the chamber circulation fan and the auxiliary/side fan; the machine can settle it. |

---

## 7. Tool-change sequence

There are **49 tool changes in the body** of `dual-extruder.gcode` (25 × `T1`, 24 × `T0`),
plus the `T1` / `T0` pair inside the start block that drives the prime line (§3).
`single-extruder.gcode` has **no** body tool changes.

```
T1 at: 746 1542 2139 2535 2931 3327 3723 4119 4515 4911 5307 5703 6099 6495 6891
       7287 7683 8079 8475 8871 9267 9663 10059 10556 11153
T0 at: 1419 2017 2413 2809 3205 3601 3997 4393 4789 5185 5581 5977 6373 6769 7165
       7561 7957 8353 8749 9145 9541 9937 10434 11031
```

### The shared framing

Every tool change, without exception, is wrapped like this:

```gcode
G1 F1200 E<current − 8.5>   ; 8.5 mm retract, absolute E, 1200 mm/min
G92 E0
<the variant body, including the T command>
```

> **Correction.** `CLAUDE.md` previously described the sequence as
> `retract → travel → G1 F1200 E8.5 → G92 E0 → T<n> → G92 E0 → M109 → M106 → G1 F1200 E8.5`,
> which reads the pre-change move as a prime. It is not. In absolute-E mode
> `G1 F1200 E18.49086` following `G1 F1800 E26.99086` is a **retract of 8.5 mm**. The
> literal `E8.5` prime appears only *after* the `T`, and only in variants B and C.

The travel before the retract always parks at the same two X positions: `X0.00 Y89.6`
before switching to T1, `X330 Y89.6` before switching to T0. Y89.6 is the model's `;MINY`.

### Variant A — the first switch to T1 only (line 746)

`sed -n '744,751p' reference/dual-extruder.gcode`

```gcode
G1 F1200 E18.49086
G92 E0
T1
G92 E0
;M105
M109 S230
M104 T0 S150
G1 F1800 E-1.5
```

Occurs **once**. T1 has never printed, so instead of priming it does the opposite: a
`-1.5` retract. It blocks on `M109 S230` because T1 is coming up from the start-block
temperature for the first time, and it parks T0 at 150 °C *after* the `T`.

### Variant B — every later switch to T1 (24 ×)

`sed -n '2136,2143p' reference/dual-extruder.gcode`

```gcode
G1 F1200 E19.27951
G92 E0
M104 T0 S150
T1
G92 E0
M104 T0 S168.3
M106 S127.5
G1 F1200 E8.5
```

- The standby drop `M104 T0 S150` moves **before** the `T` here, unlike variant A.
- The second `M104 T0 S<n>` is an interpolated ramp on the *parked* tool. It is
  non-blocking; there is no `M109`, because T1 was already at temperature.
- `M106 S127.5` is 50 % fan — T1's PETG setting.
- `G1 F1200 E8.5` restores the 8.5 mm retracted before the change.

The ramp value, in file order across the 24 occurrences:

| Line | Ramp |
|---|---|
| 1542 | `M104 T0 S150` |
| 2139 … 9663 (20 ×) | `M104 T0 S168.3` |
| 10059 | `M104 T0 S155.4` |
| 10556 | `M104 T0 S150` |
| 11153 | `M104 T0 S0` |

The last one is the final tool change of the print: T0 will not be used again, so Cura
switches it off rather than parking it.

### Variant C — every switch to T0 (24 ×)

`sed -n '2015,2022p' reference/dual-extruder.gcode`

```gcode
G1 F1200 E89.20347
G92 E0
T0
G92 E0
;M105
M109 S200
M106 S255
G1 F1200 E8.5
```

Symmetric to B except that it **blocks** on `M109 S200` and it never drops T1 to standby —
T1 stays at 230 °C the whole print. Fan is `S255`, 100 %, T0's PLA setting.

`;M105` (a commented-out temperature report) appears in A and C but not B.

### The preheat that happens outside the tool change

`M104 T0 S200` — the return of the parked hotend to full print temperature — is **not**
part of the tool-change block. It is emitted mid-print, between two extrusion moves, while
T1 is still printing:

`sed -n '1273,1277p' reference/dual-extruder.gcode`

```gcode
G1 F1350 X158.278 Y133.049 E103.63299
G0 F4200 X158.843 Y133.049
M104 T0 S200
G1 F1350 X173.048 Y118.844 E104.30115
G0 F4200 X173.048 Y119.41
```

Measured lead time, as the gap to the next `T` command:

```
$ awk '/^M104 T0 S200$/{p=NR} /^T[01]$/{if(p){print NR-p; p=0}}'
  20 × 107 lines    2 × 144 lines    2 × 152 lines    1 × 8 lines
```

So Cura looks ahead by a fixed wall-clock amount and issues the preheat early enough that
the tool is ready when the change arrives. This is a scheduling behaviour, not a block that
can be pasted anywhere.

### Fan speeds

Per-extruder and per-layer, so not reproducible from a machine profile:

```
layer 0        M107                      (off)
layer 0 end    M106 T-2 S255             (the unidentified fan, §6)
layer 1        M106 S63.8   (25 %)       dual, T1/PETG
layer 1        M106 S127.5  (50 %)       single, T0/PLA
layer 2        M106 S255    (100 %)      single, T0/PLA
tool change    M106 S127.5 / S255        whichever tool is being selected
```

---

## 8. Mapping onto OrcaSlicer

Analysis, not a decision — no JSON is written by this task. Every claim about an Orca
setting below was checked against the `v2.4.2` tag of
`/home/brad/Projects/OrcaSlicer/OrcaSlicer`, which is the version this repo targets.

| Reference block | Orca setting | Verdict |
|---|---|---|
| §2 start block | `machine_start_gcode` | **Reproducible verbatim**, with one substitution: `M140 S80` / `M190 S80` must become `[bed_temperature_initial_layer_single]`. |
| §3 prime line `B0` vs `B19` | part of `machine_start_gcode` | **Not reproducible as a constant.** Needs a conditional or a fixed choice. See `TODO.md`. |
| `M82` absolute extrusion | `use_relative_e_distances` = `0` | **Reproducible.** The base profile is wrong here — see below. |
| §4 end block | `machine_end_gcode` | **Reproducible verbatim.** The base's is Prusa-style with `{if max_layer_z …}` conditionals and is replaced wholesale. |
| §7 retract → `G92 E0` → `T` → `G92 E0` → prime | `change_filament_gcode` | **Reproducible.** The base ships this key empty. |
| §7 variant B vs C (blocking vs not) | `change_filament_gcode` | **One string cannot be both.** Task 3 must choose. |
| §7 `M104 T0 S150` standby | `ooze_prevention` + filament `idle_temperature` | **Partly.** Deferred until a second material exists. |
| §7 `M104 T0 S168.3` ramp, `M104 T0 S200` lookahead | `preheat_time` | **Different model.** Orca's ramp is not Cura's. |
| §7 fan speeds | filament fan settings | Out of scope for a single-PLA profile. |
| §6 `M106 T-2` / `M107 T-2` | — | **Unknown target.** |
| §6 `M4010`, `M2100` | — | Orca cannot emit these. |

### Why `[bed_temperature_initial_layer]` is the wrong placeholder

The base start G-code at
`git show v2.4.2:"resources/profiles/Qidi/machine/fdm_qidi_common.json"` uses

```
M140 S[bed_temperature_initial_layer] ; set final bed temp
```

`bed_temperature_initial_layer` is a placeholder-only alias (there is no config key of
that name) for a **per-filament vector** — `coInts`, `v2.4.2:PrintConfig.cpp:11316`. On a
two-extruder machine it expands to a list, which is the wrong shape for the single `M140`
the reference emits. Orca provides a resolved scalar for exactly this case:

```
v2.4.2:src/libslic3r/GCode.cpp:3034
    this->placeholder_parser().set("bed_temperature_initial_layer_single",
                                   new ConfigOptionInt(target_bed_temp));
v2.4.2:src/libslic3r/PrintConfig.cpp:11317
    "First layer bed temperature for the initial extruder.
     Same as bed_temperature_initial_layer[initial_extruder]"
```

Bed temperature is a **filament** property in Orca — the real config keys are
`hot_plate_temp` and `hot_plate_temp_initial_layer` (`v2.4.2:PrintConfig.cpp:1001`,
`1061`) — so the 80 °C itself lives in the filament profile, not the machine profile.

### Why `use_relative_e_distances` must be 0

The reference is absolute-E throughout: `M82` in the start block, and every extrusion move
in both files carries an absolute `E` value (1855 moves single, 7802 dual). The X-CF Pro
base start G-code emits `M83` — relative. Carrying the base's setting forward would
produce G-code whose `M82` header and whose moves disagree.

Confirmed present at `v2.4.2`: `use_relative_e_distances`, `ooze_prevention`,
`preheat_time`, `idle_temperature`, `standby_temperature_delta`, `change_filament_gcode`,
`machine_start_gcode` (all via
`git show v2.4.2:src/libslic3r/PrintConfig.cpp | grep 'def = this->add("<key>"'`).

### What Orca will not emit at a tool change

With `single_extruder_multi_material = 0` — which the i-Fast requires, being two
independent hotends rather than an MMU — Orca does **not** emit `G92 E0` around the tool
change (`m_writer.reset_e()` is under the SEMM branch) and does **not** emit the
tool-change temperature itself. Both therefore have to be written into
`change_filament_gcode` by hand, which is what §7's blocks provide.

### Accepted diffs for task 6

The validation harness will see these and must not treat them as failures:

- `M4010` thumbnail block — Orca has no equivalent.
- `M2100 T<seconds>` — Orca has no equivalent.
- `;SETTING_3` trailer — Cura-specific.
- All coordinates, `E` values, `;TIME`, `;TIME_ELAPSED`, `;MINX`-`;MAXZ`, `;LAYER`, and
  `;MESH` comments — different slicer, different toolpaths.

---

## 9. Corrections to earlier notes

Recorded so the next session does not re-derive them. Each of these was stated in
`CLAUDE.md` before this extraction and is wrong; `CLAUDE.md` has been updated to match.

| Was recorded as | Actually |
|---|---|
| Prime line is `G1 X330 B19 F2400` | `B19` in the dual file, `B0` in the single. §3 |
| Tool change primes `E8.5` before the `T` | That move is a **retract**; the prime is after the `T`. §7 |
| One tool-change sequence | Three variants, differing in blocking behaviour and standby placement. §7 |
| End block is 7 lines | 15 lines: also `M107 T-2`, a second `M140 S0`, `G92 E1`, and a trailing `M82` / `M104 S0`. §4 |
| Base start G-code uses `[hot_plate_temp_initial_layer]` | It uses `[bed_temperature_initial_layer]`. §8 |
| (not recorded) | The reference is absolute-E; the base profile is relative-E. §8 |
| (not recorded) | The parked hotend is preheated ~107 lines *before* the tool change. §7 |

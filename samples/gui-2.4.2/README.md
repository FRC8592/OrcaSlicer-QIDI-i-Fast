# GUI slices, OrcaSlicer 2.4.2

Two G-code files sliced **by hand, in the OrcaSlicer 2.4.2 GUI**, on 2026-09-07, from the
same 20 mm box STL the QIDI Print references were made from.

| File | Job |
|---|---|
| `20mm_Box_PLA_15m6s.gcode` | one extruder, our PLA |
| `20mm_Box_PLA_19m27s_multiple.gcode` | two extruders, our PLA in **both** slots, extruders assigned per surface |

They are kept because **the validation harness cannot produce them.** `scripts/validate.sh`
drives the CLI, and the CLI differs from the GUI in ways that matter (see below); the
2.4.2 CLI cannot slice a two-filament job at all. These are the only evidence of what the
target version actually emits for a human using the profile the intended way.

They are *our output*, not ground truth. `reference/` remains the authority.

## What they prove

Both files embed their own resolved config (`; CONFIG_BLOCK_START`), and it reads:

```
; printer_settings_id  = QIDI i-Fast 0.4 nozzle
; print_settings_id    = 0.20mm Standard @QIDI i-Fast
; filament_settings_id = "QIDI Generic PLA @QIDI i-Fast";"QIDI Generic PLA @QIDI i-Fast"
; printable_area = 0x0,330x0,330x250,0x250     ; printable_height = 320
; nozzle_diameter = 0.4,0.4                    ; single_extruder_multi_material = 0
; use_relative_e_distances = 0                 ; initial_layer_print_height = 0.3
; enable_prime_tower = 0                       ; disable_m73 = 1
; support_air_filtration = 0                   ; manual_filament_change = 0
; machine_max_acceleration_e = 5000,5000,5000,5000
; curr_bed_type = High Temp Plate              ; hot_plate_temp = 80,80
```

- All three presets load and resolve in the GUI, with no substitution.
- `inherits` resolves: every value above comes through the chain, not from a flattened file.
- `curr_bed_type = High Temp Plate` — the GUI **does** honour `default_bed_type: "3"`,
  where the CLI falls back to Cool Plate. Both paths now emit `M140 S80` / `M190 S80`.
- Zero `M900`, zero `M106 P<n>`, zero `M73`, zero `;TIMELAPSE_TAKE_FRAME`, zero
  `;BEFORE_LAYER_CHANGE`, no `M83`. First layer at `Z0.3`.
- End block **byte-identical** to the reference in both files.
- Start block identical to the reference apart from the T1 heating temperature (our PLA
  at 200 °C against the reference's PETG at 230 °C), and the `is_extruder_used[1]`
  conditional behaves in both directions: the single file comments the `T1` pair out and
  primes `B0`, the dual file leaves them live and primes `B19` — exactly as
  `single-extruder.gcode` and `dual-extruder.gcode` respectively do.
- **The tool-change block runs on the target version**: all 51 body tool changes in the
  dual file are `T<n>` / `G92 E0` / `M109 S200`, our `change_filament_gcode` verbatim,
  26 to T0 and 25 to T1, each preceded by Orca's own retract + wipe + `G92 E0` and
  followed by a `G1 E2` prime — 50 of 51, the exception being the initial tool
  selection, which has no retraction to undo.
- **The 2.4.2 GUI slices a two-filament job without trouble.** The `std::vector`
  out-of-range abort recorded in `TODO.md` is a CLI-only bug.

## Reproducing the comparison

```bash
python3 scripts/gcode_diff.py reference/single-extruder.gcode \
    "samples/gui-2.4.2/20mm_Box_PLA_15m6s.gcode" --context single

python3 scripts/gcode_diff.py reference/dual-extruder.gcode \
    "samples/gui-2.4.2/20mm_Box_PLA_19m27s_multiple.gcode" --context dual --toolchange
```

Both report differences the harness's own runs do not, and the differences are real, not
noise — they are listed in `TODO.md` under "Found by the 2.4.2 GUI slices". Two of them
matter:

1. The single-extruder file emits **one bare `T0`** after the preamble that neither the
   reference nor the CLI slice has.
2. The dual file's tool-change *count* and surface assignment differ from the reference's
   by construction — the user assigned extruders to different surfaces — so tool-change
   counts (51 against 49) are a property of the job, not of the profile.

#!/usr/bin/env bash
#
# Task 6 (see intent/0001-orcaslicer-profile-for-the-ifast.md): slice the shipped
# profiles and diff
# the result against the QIDI Print reference exports.
#
#   bash scripts/validate.sh
#
# Everything is regenerated under out/validate/, which is gitignored.  The run
# exits non-zero if any difference is not in scripts/accepted.py's registry, or
# if the dual-extruder slice fails to produce a body tool change.
#
# Environment overrides:
#   ORCA_CMD         slicer to use (default: the 2.4.2 flatpak, the target)
#   ORCA_SYSTEM_DIR  OrcaSlicer's installed Qidi system bundle
#   ORCA_DUAL_CMD    slicer for the dual case only; see the note below
#   DUAL_FILAMENT2   second-slot filament preset for the dual case
#
# Note: the dual invocation deliberately omits --allow-mix-temp. 2.3.1 has no
# such option ("setup params error") and does not need it for PLA + PETG. If a
# later OrcaSlicer rejects the pair with "Selected nozzle temperatures are
# incompatible", add `--allow-mix-temp 1` to slice_dual below.
#
# Why ORCA_DUAL_CMD exists: the OrcaSlicer 2.4.2 CLI aborts on *any* two-filament
# slice with a std::vector out-of-range assertion, before it emits anything.
# This is not a defect in these profiles — it reproduces with OrcaSlicer's own
# stock `Lulzbot Taz Pro Dual 0.5 nozzle` preset, and with a single-nozzle
# machine.  The 2.3.1 AppImage slices the same flattened presets fine, so it is
# used as a fallback to get the tool-change evidence, clearly labelled.

set -u -o pipefail

cd "$(dirname "$0")/.."
REPO=$PWD
OUT=$REPO/out/validate

ORCA_CMD=${ORCA_CMD:-"flatpak run com.orcaslicer.OrcaSlicer"}
ORCA_SYSTEM_DIR=${ORCA_SYSTEM_DIR:-"$HOME/.var/app/com.orcaslicer.OrcaSlicer/config/OrcaSlicer/system/Qidi"}
ORCA_DUAL_CMD=${ORCA_DUAL_CMD:-"$HOME/Applications/OrcaSlicer_Linux_AppImage_Ubuntu2404_V2.3.1.AppImage"}
# The reference's dual job is PLA on T0 and PETG on T1.  OrcaSlicer's stock
# `Qidi Generic PETG` is a legacy-generation preset (it names Qidi X-Max 0.4
# nozzle in its own compatible_printers), used here as a *test fixture only* —
# it is not shipped in profiles/ and no value in this repo is sourced from it.
DUAL_FILAMENT2=${DUAL_FILAMENT2:-"$ORCA_SYSTEM_DIR/filament/Qidi Generic PETG.json"}

MACHINE="profiles/machine/QIDI i-Fast 0.4 nozzle.json"
PROCESS="profiles/process/0.20mm Standard @QIDI i-Fast.json"
FILAMENT="profiles/filament/QIDI Generic PLA @QIDI i-Fast.json"

say() { printf '%s\n' "$*" >&2; }

if [ ! -d "$ORCA_SYSTEM_DIR" ]; then
	say "error: OrcaSlicer's Qidi system bundle is not at $ORCA_SYSTEM_DIR."
	say "       Run OrcaSlicer's configuration wizard once and enable a QIDI printer,"
	say "       or point ORCA_SYSTEM_DIR at the bundle."
	exit 2
fi

rm -rf "$OUT"
mkdir -p "$OUT"/{presets,models,single,dual}

# ---------------------------------------------------------------- presets ----
# The CLI does not resolve `inherits` (v2.4.2:src/OrcaSlicer.cpp:1953-2020), so
# a thin preset silently loses every inherited QIDI value.  Flatten first.
say "== flattening presets against $ORCA_SYSTEM_DIR"
python3 scripts/flatten.py "$MACHINE"  --system-dir "$ORCA_SYSTEM_DIR" -o "$OUT/presets/machine.json"  || exit 2
python3 scripts/flatten.py "$PROCESS"  --system-dir "$ORCA_SYSTEM_DIR" -o "$OUT/presets/process.json"  || exit 2
python3 scripts/flatten.py "$FILAMENT" --system-dir "$ORCA_SYSTEM_DIR" -o "$OUT/presets/filament.json" || exit 2
python3 scripts/flatten.py "$DUAL_FILAMENT2" --system-dir "$ORCA_SYSTEM_DIR" -o "$OUT/presets/filament2.json" || exit 2

say "== generating models"
python3 scripts/make_models.py "$OUT/models" >/dev/null || exit 2

# ------------------------------------------------------------------ slice ----
# The slicer runs inside a flatpak sandbox that cannot see /tmp, so every input
# and output path has to live under the repo.
slice_single() {
	say "== slicing single-extruder case with: $ORCA_CMD"
	$ORCA_CMD \
		--load-settings "$OUT/presets/machine.json;$OUT/presets/process.json" \
		--load-filaments "$OUT/presets/filament.json" \
		--slice 0 --export-3mf out.gcode.3mf --outputdir "$OUT/single" \
		"$OUT/models/cube20.stl" >"$OUT/single/slicer.log" 2>&1
}

slice_dual() {  # $1 = slicer command, $2 = output dir
	mkdir -p "$2"
	# $1 is deliberately unquoted: it may be a multi-word command such as
	# "flatpak run com.orcaslicer.OrcaSlicer".
	$1 \
		--load-settings "$OUT/presets/machine.json;$OUT/presets/process.json" \
		--load-filaments "$OUT/presets/filament.json;$OUT/presets/filament2.json" \
		--load-filament-ids "1,2" --arrange 1 \
		--slice 0 --export-3mf out.gcode.3mf --outputdir "$2" \
		"$OUT/models/cube20_a.stl" "$OUT/models/cube20_b.stl" >"$2/slicer.log" 2>&1
}

slice_single
SINGLE_RC=$?
if [ ! -s "$OUT/single/plate_1.gcode" ]; then
	say "error: the single-extruder slice produced no G-code (exit $SINGLE_RC)."
	tail -5 "$OUT/single/slicer.log" >&2
	exit 2
fi

say "== slicing dual-extruder case with: $ORCA_CMD"
DUAL_SLICER="$ORCA_CMD"
DUAL_NOTE=""
slice_dual "$ORCA_CMD" "$OUT/dual"
if [ ! -s "$OUT/dual/plate_1.gcode" ]; then
	PRIMARY_ERR=$(tail -2 "$OUT/dual/slicer.log")
	say "   the target slicer did not produce G-code; falling back to ORCA_DUAL_CMD"
	if [ -x "${ORCA_DUAL_CMD%% *}" ]; then
		slice_dual "$ORCA_DUAL_CMD" "$OUT/dual"
		DUAL_SLICER="$ORCA_DUAL_CMD"
		DUAL_NOTE="The target slicer (\`$ORCA_CMD\`) could not produce this slice:

\`\`\`
$PRIMARY_ERR
\`\`\`

It aborts on **any** two-filament CLI slice, before emitting anything.  This is
not a defect in these profiles: it reproduces with OrcaSlicer's own stock
\`Lulzbot Taz Pro Dual 0.5 nozzle\` preset and with a single-nozzle machine.
The comparison below was therefore produced with \`$ORCA_DUAL_CMD\`, which
slices the same flattened presets successfully — **so it is evidence about the
profile's tool-change block, not about the target version's output.**"
	else
		DUAL_NOTE="No dual-extruder slice could be produced. The target slicer aborted:

\`\`\`
$PRIMARY_ERR
\`\`\`

and no fallback slicer was found at \`$ORCA_DUAL_CMD\`."
	fi
fi

# ------------------------------------------------------------------ diffs ----
STATUS=0
python3 scripts/gcode_diff.py reference/single-extruder.gcode "$OUT/single/plate_1.gcode" \
	--title "Single-extruder case" --context single -o "$OUT/single.md" >/dev/null || STATUS=1

if [ -s "$OUT/dual/plate_1.gcode" ]; then
	python3 scripts/gcode_diff.py reference/dual-extruder.gcode "$OUT/dual/plate_1.gcode" \
		--title "Dual-extruder case" --context dual --toolchange -o "$OUT/dual.md" >/dev/null || STATUS=1
	TC=$(grep -c '^T[01]$' "$OUT/dual/plate_1.gcode")
	if [ "$TC" -le 2 ]; then
		say "error: the dual slice emitted only $TC T commands — the start block's"
		say "       prime pair and nothing else. The tool-change check is vacuous."
		STATUS=1
	fi
else
	printf '## Dual-extruder case\n\nBLOCKED — no G-code was produced.\n' > "$OUT/dual.md"
	STATUS=1
fi

{
	echo "# QIDI i-Fast profile — validation report"
	echo
	echo "Produced by \`scripts/validate.sh\`. Regenerate with the same command;"
	echo "the report is deterministic for a given slicer and profile set."
	echo
	echo "## Environment"
	echo
	echo "| | |"
	echo "|---|---|"
	echo "| single-extruder slicer | \`$ORCA_CMD\` |"
	echo "| dual-extruder slicer | \`$DUAL_SLICER\` |"
	echo "| system bundle | \`${ORCA_SYSTEM_DIR/#$HOME/\~}\` |"
	echo "| machine preset | \`$MACHINE\` |"
	echo "| process preset | \`$PROCESS\` |"
	echo "| filament preset | \`$FILAMENT\` |"
	echo "| second filament (fixture) | \`${DUAL_FILAMENT2/#$HOME/\~}\` |"
	echo
	cat "$OUT/single.md"
	echo
	if [ -n "$DUAL_NOTE" ]; then
		echo "> **Note on the dual-extruder case.**"
		echo
		printf '%s\n' "$DUAL_NOTE"
		echo
	fi
	cat "$OUT/dual.md"
} > "$OUT/report.md"

say
say "== report written to out/validate/report.md"
grep -E '^- \*\*[0-9]+ accepted' "$OUT/report.md" >&2 || true
if [ "$STATUS" -ne 0 ]; then
	say "== FAIL: undocumented differences (or a blocked check) — see the report"
else
	say "== PASS: every difference is documented. 'known-unresolved' counts the"
	say "         ones still awaiting a decision in TODO.md; they are reported in"
	say "         full every run and are not hidden."
fi
exit $STATUS

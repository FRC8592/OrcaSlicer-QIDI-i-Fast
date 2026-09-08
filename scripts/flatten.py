#!/usr/bin/env python3
"""Resolve an OrcaSlicer preset's `inherits` chain into a single flat JSON file.

The OrcaSlicer CLI reads every --load-settings / --load-filaments file raw: the
inherits-handling branches in load_config_file are commented out
(v2.4.2:src/OrcaSlicer.cpp:1953-2020, see :1987 and :1991), and any key absent
from the file falls back to OrcaSlicer's built-in FFF default when
m_print_config.apply(fff_print_config, true) runs at :3629.  A thin preset that
is perfectly correct in the GUI therefore loses every inherited QIDI value from
the CLI, silently.  This script does the resolution the CLI does not.

Three keys are deliberately preserved in the output:

  inherits    the CLI derives new_printer_system_name from it (:2045); stripping
              it makes the compatible_printers check fail with -17
  from        mandatory, must be "system" / "User" / "user" or the CLI exits -5
              with `file <x>'s from  unsupported` (:1975-1979)
  filament_id read from the same key-value map for filament presets (:1993-1995)

and two are dropped: `instantiation`, which the CLI does not read, and
`setting_id`, which would otherwise be inherited from the *parent* preset and so
name the wrong thing.
"""

import argparse
import json
import os
import sys

# Keys that must never be inherited from a parent: they identify the preset.
DROP = ("instantiation", "setting_id")
# Keys the child always owns, even though the parent has them too.
CHILD_OWNS = ("name", "inherits", "from", "type")

SUBDIRS = ("machine", "process", "filament")


def find_preset(system_dir, name):
    for sub in SUBDIRS:
        path = os.path.join(system_dir, sub, name + ".json")
        if os.path.exists(path):
            return path
    return None


def chain(preset_path, system_dir):
    """Return [root, ..., parent, child] — the presets to merge, in order."""
    with open(preset_path, encoding="utf-8") as fh:
        child = json.load(fh)
    presets = [child]
    seen = {os.path.abspath(preset_path)}
    name = child.get("inherits")
    while name:
        path = find_preset(system_dir, name)
        if path is None:
            sys.exit("flatten: cannot resolve inherits %r under %s" % (name, system_dir))
        if os.path.abspath(path) in seen:
            sys.exit("flatten: inherits cycle at %r" % name)
        seen.add(os.path.abspath(path))
        with open(path, encoding="utf-8") as fh:
            parent = json.load(fh)
        presets.append(parent)
        name = parent.get("inherits")
    presets.reverse()
    return presets


def flatten(preset_path, system_dir):
    presets = chain(preset_path, system_dir)
    child = presets[-1]
    out = {}
    for preset in presets:
        for key, value in preset.items():
            if key in DROP or key in CHILD_OWNS:
                continue
            out[key] = value
    # The child owns its own identity; an inherited `from` would say "system".
    for key in CHILD_OWNS:
        if key in child:
            out[key] = child[key]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("preset", help="path to the user preset JSON")
    ap.add_argument("--system-dir", required=True,
                    help="OrcaSlicer system bundle dir, e.g. <config>/system/Qidi")
    ap.add_argument("-o", "--output", help="write here instead of stdout")
    ap.add_argument("--set-name", help="override the flattened preset's name")
    args = ap.parse_args()

    flat = flatten(args.preset, args.system_dir)
    if args.set_name:
        flat["name"] = args.set_name
    text = json.dumps(flat, indent="\t", ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()

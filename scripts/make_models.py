#!/usr/bin/env python3
"""Generate the binary STL test models the validation harness slices.

`out/` is gitignored, so the models are regenerated rather than committed.  They
are plain axis-aligned cubes: the harness compares G-code *structure* — start
block, end block, temperature commands, M-codes, tool-change shape — and
explicitly ignores coordinates, so the model geometry only has to be valid and
deterministic, not representative.

Two cubes are written for the dual-extruder case because OrcaSlicer's CLI
assigns extruders per *input file*: `--load-filament-ids "1,2"` sets
ModelObject::config["extruder"] on every object loaded from the corresponding
positional argument (v2.4.2:src/OrcaSlicer.cpp:1798-1807, :1839-1849).  One
object per file is therefore the only way to get one object per extruder.
"""

import argparse
import os
import struct

# The 12 triangles of a unit cube, as (v0, v1, v2) vertex-index triples over the
# 8 corners below, wound counter-clockwise seen from outside.
CORNERS = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
           (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
FACES = [(0, 3, 2), (0, 2, 1),   # bottom
         (4, 5, 6), (4, 6, 7),   # top
         (0, 1, 5), (0, 5, 4),   # front  (-Y)
         (1, 2, 6), (1, 6, 5),   # right  (+X)
         (2, 3, 7), (2, 7, 6),   # back   (+Y)
         (3, 0, 4), (3, 4, 7)]   # left   (-X)


def cube(path, size, origin):
    ox, oy, oz = origin
    verts = [(ox + x * size, oy + y * size, oz + z * size) for x, y, z in CORNERS]
    with open(path, "wb") as fh:
        fh.write(b"qidi-ifast-profile validation cube".ljust(80, b"\0"))
        fh.write(struct.pack("<I", len(FACES)))
        for a, b, c in FACES:
            # A zero normal is legal and tells the reader to derive it from the
            # winding; OrcaSlicer flips the winding itself if the volume comes
            # out negative (v2.4.2:bbs_3mf.cpp / TriangleMesh).
            fh.write(struct.pack("<3f", 0.0, 0.0, 0.0))
            for idx in (a, b, c):
                fh.write(struct.pack("<3f", *verts[idx]))
            fh.write(struct.pack("<H", 0))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("outdir")
    ap.add_argument("--size", type=float, default=20.0)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    s = args.size
    # Single case: one cube at the origin; the CLI arranges it onto the plate.
    cube(os.path.join(args.outdir, "cube20.stl"), s, (0.0, 0.0, 0.0))
    # Dual case: two cubes, already separated so they are never coincident even
    # if arranging is skipped.
    cube(os.path.join(args.outdir, "cube20_a.stl"), s, (0.0, 0.0, 0.0))
    cube(os.path.join(args.outdir, "cube20_b.stl"), s, (2.0 * s, 0.0, 0.0))
    for name in ("cube20.stl", "cube20_a.stl", "cube20_b.stl"):
        print(os.path.join(args.outdir, name))


if __name__ == "__main__":
    main()

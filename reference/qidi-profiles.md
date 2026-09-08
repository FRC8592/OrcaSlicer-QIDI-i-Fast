# QIDI's published legacy profile bundle — not in this repo

This repo reads QIDI's own published slicer profiles as a source of provenance, but does
**not** redistribute them. They are QIDI's files, not ours. Download them yourself; this
page tells you exactly which ones, where they come from, and how to confirm you got the
same bundle these notes were written against.

## Where to get it

1. Open QIDI's software page: <https://qidi3d.com/pages/software-firmware>
2. Find **"QIDI Other Series Printer Profiles"** — the entry covering i-Fast, X-CF Pro,
   X-Max and X-Plus, linked as *"Cura, Prusa-Slicer, Simplify3D, ideaMaker etc"*.
3. It links a Google Drive folder:
   <https://drive.google.com/drive/folders/1I2IbPXjcXrCj-nLF0E4uU5uUVE3SOlNH?usp=share_link>
4. Unpack it to `reference/qidi-profiles/` if you want the paths in this repo's notes to
   resolve on disk. `.gitignore` excludes that directory, so it cannot be committed back.

The same page also offers **QIDI Print 6.5.4** (2/2023) under the legacy-printer section.
That is the slicer that produced [`single-extruder.gcode`](single-extruder.gcode) and
[`dual-extruder.gcode`](dual-extruder.gcode) — the two files in this repo that *are* the
ground truth, because they are our own exports rather than QIDI's distribution.

## What this repo's provenance actually depends on

Only three files. Everything else in the bundle was read for cross-checking and never
sourced from.

| File in the bundle | What it establishes |
|---|---|
| `prusaslicer/PrusaSlicer_fast.ini` | The i-Fast's geometry and dual-extruder configuration: `bed_shape = 0x0,330x0,330x250,0x250`, `max_print_height = 320`, `extruder_offset = 0x0,0x0`, `single_extruder_multi_material = 0`, `gcode_flavor = marlin`, `nozzle_diameter = 0.4,0.4`, and the motion limits. Note the conflict resolved in favour of the G-code: this ini says bed 60 °C where the reference emits `M140 S80`. |
| `CURA/qidi.zip` → `qidi/definitions/qidi.def.json` | The shared QIDI Cura definition — the speeds and retraction QIDI Print slices with, cross-checked during the first-print review. |
| `CURA/qidi.zip` → `qidi/definitions/i-fast.def.json` | The i-Fast's own Cura definition, inheriting the above. |

`simplify3D/`, `ideaMaker/` and `slic3r/` hold sibling-machine profiles (`_max`, `_plus`,
`_pro`, `_cf_pro`, `_maker`, `_mates`, and the i-Fast's own). They were useful for
cross-checking and are **never** a source of i-Fast values — see hard rule 1 in
[`../CLAUDE.md`](../CLAUDE.md).

`CURA/qidi.zip` also contains `qidi/meshes/*.STL` (bed models) and a
`cura add qidi printer.mp4` tutorial, which together are ~61 MB of the archive's 38 MB
compressed. Nothing in this repo reads them.

## Manifest

What was read, as it was on disk when these notes were written. Compare against your own
download to confirm you have the same files.

```
sha256                                                               bytes  path
37689fb74acb29b539104aa05cd655f8407f051b350232c2841194c5abc211e7    119137  CURA/cura.pdf
6ed48ce94c6876d5e42596e3b6b48be5eb1e501921faae9d6ffbe0fbe71a06b0  38074263  CURA/qidi.zip
350bf8357a275caa71b37a257d40ad7677205750707981504c230c6cca53badf      3369  ideaMaker/i-fast-export.printer
c6761301db77649f6c6f5d41a284921180847a3545f670dddaafecc9d6058c6a     23800  ideaMaker/i-fast-PLA-export.bin
ec9fab431d948dfc740f42f5e2b61db9c4f1cb26e1530f0d35157927ba3e1273      3163  ideaMaker/i-mates-export.printer
0e98d7b5c28d43c1780938a2b41dd4873b38880b58512aa29200151ca7471f73     24134  ideaMaker/i-mates-PLA-export.bin
9cc51e4b99873af07f1273d2b38b0497ce78c2da49f20d70970afd26f0e4c23f      3161  ideaMaker/X-MAX-export.printer
efebc81327954b62c87d37285fa0e2508086bb3219a14e70bc92d29afcb66a05     24122  ideaMaker/X-MAX-PLA-export.bin
888422f73888609151c1f7c70243ee271e72a3b751c15d2197e30a652676f847      8032  prusaslicer/PrusaSlicer_cf_pro.ini
333c15b1b31a9af3989a206146892839fe98fef4e9b5f44c07068134dd996098      8549  prusaslicer/PrusaSlicer_fast.ini
54f9cc236c0f6623625e7c83934df6418ddbcfaa36c71c6ecbc8f19360126a4e      8029  prusaslicer/PrusaSlicer_maker.ini
1b42f4dcca24e180e7b4df46ffddd7d89719e908902b742a82b3ac2759480789      8029  prusaslicer/PrusaSlicer_mates.ini
f248fe08d2b7172ccdac2006e88bde041410e05d110c3f199238be8fed81bf9c      8023  prusaslicer/PrusaSlicer_max.ini
e02e44ae13ce07ef0bf405a93ccf0b09086d8e1d9d9f2516315dbf19a4fabae4      8026  prusaslicer/PrusaSlicer_plus.ini
6611b1d50d083ce0db1015538f1242ddcadc8f58dab1e27e5ef548c5e38215f2      8488  prusaslicer/PrusaSlicer_pro.ini
68912f1d384b45c5935bbee7d677d00223738dc6d10248d8c6fb4c2f63e409df     24315  simplify3D/Qidi Technology i-fast.fff
a1f07d5bd9d53a3bb44b5116a7f6ab969c9dc858728704ef6cf4640beb273603     11818  simplify3D/Qidi Technology i-mate.fff
2c5f3edbded9212f22e1cedc60b60f100101c93d9b5a9d513ec7ee4a39285090     29392  simplify3D/Qidi Technology Qidi Tech I.fff
97682765e71fe120e5ef4ae9cbe1e05d864ebc66d79d1941605c26e1d1d30e5b     12007  simplify3D/Qidi Technology X-Maker.fff
fc39c1ceaf9d8d35576e4149c0b3edf80907035a3e35a6aea4ca316ea3c50b3d     12005  simplify3D/Qidi Technology X-Max.fff
14f7f9cb48715cc374d3b2e30eab1823c1da39c35bd007578fa0a5aceb1c72f6     12010  simplify3D/Qidi Technology X-one2.fff
065a203da72025a8f0a3f95163ae9f471edafa17b4bda137420a8271f03756dc     12006  simplify3D/Qidi Technology X-Plus.fff
700756c3563b2d1325d6a798eddf381c46eee47eff1e59a689feb150aaba1550     26791  simplify3D/Qidi Technology X-pro.fff
08c93a29984afb333ad46f30943e408ea0a9fe2f02e2d66ca94dcffe7aeeb42b     12007  simplify3D/Qidi Technology X-Smart.fff
1dcd074888c847d4e983ae7aa6f5dcccee701c3bd528fa5c1b8501f83426691b      4721  slic3r/x-cf pro.ini
00f7aa36857f309f22644f4b7862395f29763b6a8fd4d8da4e476c793ea9488a      4623  slic3r/x-maker.ini
3672e2943189a026e66cf930c21ab642f077c044b3f99a8d77455cf69b2b80d6      4768  slic3r/x-max.ini
80113b827d2f1de0b43fb0c7cbc3741e0c8e37b8b3dd04e76c9be7a4c41a44e4      4721  slic3r/x-plus.ini
```

28 files, 38,503,509 bytes in total, of which `CURA/qidi.zip` alone is 38,074,263.

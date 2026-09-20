# Intent: get sliced G-code onto the i-Fast over WiFi
Author: Brad Sneade. Status: **open**.

> Written on 2026-09-09 from `HANDOFF.md`, a session handoff that fused the intent with
> its design, its recon and its next steps. That file was folded into this one and
> removed. Unlike [`0001`](0001-orcaslicer-profile-for-the-ifast.md) and
> [`0002`](0002-first-print-and-physical-verification.md) this is **not profile work** —
> it touches nothing under [`profiles/`](../profiles/) and changes no sliced value. It is
> recorded here because it is the next thing wanted from this machine, and because the
> protocol facts below cost a session to establish and are not written down anywhere else
> in the repo.

## Problem

The profile is done; getting a file to the printer is not. Every slice ends the same way:
export to a USB stick, walk to the machine, plug it in. The i-Fast is on the LAN and
answers to a network stack — the stick is pure friction.

OrcaSlicer cannot close that gap on its own. Its **Add physical printer** dialog offers
OctoPrint, Duet, FlashAir, Repetier, PrusaLink, Moonraker and the rest; the i-Fast speaks
none of them. It runs QIDI's proprietary firmware on a ChiTu F Plus board and takes files
over a **plain-text UDP protocol on port 3000**. There is no host type that matches, and
so no way to make Orca's Upload button work short of patching Orca.

The confusion worth naming up front, because every search result runs into it: QIDI's
*Klipper* machines — Max 3, Plus 4, Q1 Pro, X-Smart 3 — do have Moonraker, on port
**10088** rather than the usual 7125, and QIDI's own wiki documents that as if it were
advice about QIDI printers generally. It is not. It does not apply to the i-Fast, which is
the [legacy generation](../CLAUDE.md#the-machine). (My Max 3 is set up that way and works:
Host Type `Klipper host`, Hostname `http://<ip>:10088`, API key blank. That machine is not
what this is about.)

## Proposed outcome

Slicing in Orca ends with the file already on the printer, with no stick and no second
application — and without ever starting a print as a side effect of exporting one.

Good enough looks like: I hit Export in Orca, and the file shows up in the i-Fast's file
list. Starting the print stays a deliberate, separate act.

## Inputs assumed present

This work is not starting from nothing. The following were established live against the
printer and should not be re-researched:

- **The machine answers.** Live replies came back from `M4001` (handshake — returns
  steps/mm and geometry, reporting a bed of 372 × 250 × 321), `M4002` (firmware version),
  `M119` (temperatures), `M20` (file list, which came back **empty**) and `M27` (progress,
  `Error:It's not printing now!` when idle). Writing a file is `M28 <name>` → data blocks
  → `M29 <name>`; printing one is `M6030 ":<name>" I1`.
- **The data-block framing**, verified byte-for-byte against QIDI's own implementation:
  up to 1280 bytes of payload, then a 4-byte little-endian file offset, then a 1-byte XOR
  checksum over every byte from index 0 through the last offset byte inclusive, then
  `0x83`. A block is answered with `ok` or with `resend <offset>`.
- **Two session behaviours that read as failures and are not.**
  `Error:Wifi reboot,please reconnect!` is the module resetting its session when a new
  client appears — the first `M4001` from any new client reliably gets it; resend and it
  works. `Error:IP is connected by IP:x.x.x.x already!` means the module has bound to a
  single client **source port**: one socket must serve a whole session, and QIDI Print
  must be closed.
- **The protocol reference**: QIDI's own Cura plugin,
  [`QidiConnectionManager.py`](https://github.com/MarkoS046/QidiPrint). Also seen and
  judged less useful: [3dWiFiSend](https://github.com/yandreev3/3dWiFiSend), an older
  X-Pro/X-Max script that works via the USB drive.
- **The uploader is written**: [`qidi_send.py`](../qidi_send.py) at the repo root, ~11 KB,
  stdlib only, Python 3. It handles the handshake and config parse, the WiFi-reboot retry,
  one socket per session, `resend` recovery, progress to stderr, ASCII filename
  sanitisation, and `SLIC3R_PP_OUTPUT_NAME` for the printer-side name. Modes:

  ```bash
  python3 qidi_send.py --ip <printer-ip> --status               # read-only probe
  python3 qidi_send.py --ip <printer-ip> model.gcode            # upload only
  python3 qidi_send.py --ip <printer-ip> --print model.gcode    # upload + START PRINTING
  python3 qidi_send.py --ip <printer-ip> --compress model.gcode # use VC_compress if present
  ```

  `--print` is deliberately off by default, so an export cannot start a print by accident.
  `<printer-ip>` stands for the machine's address on the LAN throughout this repo; the
  real one is not written down here, and `--ip` has no default — the script refuses to
  run without it.
- **`VC_compress_gcode`** — QIDI's closed-source compressor, which produces the `.gcode.tz`
  the printer wants for an on-screen preview and time estimate — is **not on this Mac**.
  Only `/Applications/QIDISlicer.app` is installed and does not bundle it. Plain `.gcode`
  uploads are expected to work, minus the preview and the estimate.

## Affected users and systems

Me, and the physical i-Fast at its fixed address on my LAN. On the Orca side this is a
**post-processing script** on the print profile, not a printer setting — Orca appends the
sliced file path to the command and runs it on export, which is the closest thing to an
Upload button that exists for this protocol. The hook is Print Settings → Others →
Post-processing Scripts, and the line that was in use read:

```
/usr/bin/python3 "/Users/brad/bin/qidi_send.py" --ip <printer-ip> --quiet;
```

Nothing in [`profiles/`](../profiles/) is touched. The script sits at the repo root, which
is a placement rather than a decision — [`scripts/`](../scripts/) currently means *the
validation harness*, and neither [`README.md`](../README.md) nor
[`CLAUDE.md`](../CLAUDE.md) §"Repo layout" mentions the uploader at all.

## Constraints

- **Hard rule 3** ([`CLAUDE.md`](../CLAUDE.md) §"Hard rules") stands unchanged: no network
  or print-host configuration in the profile, because Orca has no host type that fits.
  This work does not relax that rule — it routes around it, outside the profile entirely.
  [`README.md`](../README.md) §"Deliberately not configured" stays true.
- **Never start a print as a side effect.** `M6030` puts plastic on a bed in a room I may
  not be in. Uploading and printing must be separate, printing must be opt-in, and the
  first `M6030` of any session needs me to say so out loud.
- **The first real upload is asked about first** — it writes to the printer's storage.
  Small file, obvious name, no print flag, confirmed visible on the touchscreen or via
  `M20`.
- Stdlib-only Python 3, single file, no install step. It has to survive me forgetting it
  exists for a year.
- Not a Klipper conversion, not an OctoPrint box. Both were considered and rejected as a
  different size of project than the one I want; see below.

## Open questions

The live list is [`TODO.md`](../TODO.md) §"WiFi upload to the i-Fast", which is where
these get worked and ticked — reachability and the read-only probe, the first real upload
and the consent around it, where the script lives and whether the repo admits it exists,
and what is still unverified inside the script itself. Not duplicated here, or the two
drift.

Two that shape the intent rather than the task list:

- **The printer reports a bed this repo does not.** `M4001` returns `T:0/372/250/321/2`
  against the 330 × 250 × 320 the profile carries from QIDI's own `PrusaSlicer_fast.ini`.
  Probably firmware reporting axis travel rather than printable area — a second head has
  to park somewhere — but if it is not, a shipped value is wrong. It is a *profile*
  question that only this workstream would ever have surfaced, so it is filed under
  [`TODO.md`](../TODO.md) §"Found by the WiFi work", not here.
- **Is the manual route good enough?** Slicing in Orca, exporting, and sending from QIDI
  Print works today with zero setup. If the script cannot be made reliable, that is the
  fallback and this intent gets dropped rather than fought.

#!/usr/bin/env python3
"""Send a G-code file to a QIDI printer that speaks the ChiTu WiFi protocol
(i-Fast, X-Pro, X-Max, X-Plus -- the pre-Klipper machines) over UDP port 3000.

Designed to be usable as an OrcaSlicer post-processing script:

    /usr/bin/python3 /path/to/qidi_send.py --ip 192.168.213.87;

Orca appends the sliced G-code path as the final argument. Add --print to start
the print immediately after upload (off by default -- upload only).

Protocol reference: QIDI's own Cura plugin (QidiConnectionManager.py).
"""

import argparse
import os
import re
import socket
import struct
import subprocess
import sys
import time

PORT = 3000
BUFSIZE = 1280
BLOCK_TERMINATOR = 0x83

# QIDI's closed-source G-code compressor, shipped inside QIDI Print on macOS.
MAC_COMPRESSOR_PATHS = [
    "/Applications/QIDI Print.app/Contents/Resources/VC_compress_gcode_MAC",
    "/Applications/QIDI-Print.app/Contents/Resources/VC_compress_gcode_MAC",
]


class QidiError(Exception):
    pass


class QidiPrinter:
    def __init__(self, ip, timeout=2.0, retries=3, verbose=True):
        self.ip = ip
        self.timeout = timeout
        self.retries = retries
        self.verbose = verbose
        self.encoding = "utf-8"
        self.config = {}
        # One socket -- and therefore one source port -- for the whole session.
        # The WiFi module binds to a single client and rejects a second one with
        # "Error:IP is connected by IP:x.x.x.x already!".
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(self.timeout)

    def log(self, msg):
        if self.verbose:
            print(msg, file=sys.stderr)

    def close(self):
        self.sock.close()

    def _drain(self):
        self.sock.settimeout(0)
        try:
            while True:
                self.sock.recvfrom(8192)
        except (BlockingIOError, socket.timeout, OSError):
            pass
        finally:
            self.sock.settimeout(self.timeout)

    def request(self, cmd, retries=None):
        """Send a command (str or bytes) and return the decoded reply."""
        retries = self.retries if retries is None else retries
        payload = cmd.encode(self.encoding, "ignore") if isinstance(cmd, str) else cmd
        last = ""
        for attempt in range(retries):
            self._drain()
            try:
                self.sock.sendto(payload, (self.ip, PORT))
                data, _ = self.sock.recvfrom(8192)
            except socket.timeout:
                last = "<timeout>"
                continue
            except OSError as exc:
                # EHOSTUNREACH shows up while the WiFi module is rebooting.
                last = f"<{exc.strerror}>"
                time.sleep(1.0)
                continue
            msg = data.decode(self.encoding, "ignore")
            if "Error:Wifi reboot" in msg:
                # The module resets its session for a new client; the next
                # attempt is the one that lands.
                last = msg.strip()
                time.sleep(0.5)
                continue
            if "Error:IP is connected" in msg:
                raise QidiError(
                    "Printer is already claimed by another client "
                    f"({msg.strip()}). Close QIDI Print, or wait for its "
                    "session to time out, then retry."
                )
            return msg
        raise QidiError(f"No usable reply to {cmd!r} after {retries} attempts (last: {last})")

    def connect(self):
        msg = self.request("M4001").strip()
        self.log(f"handshake: {msg}")
        for item in msg.split(" "):
            key, _, value = item.partition(":")
            if not _:
                continue
            if key in ("X", "Y", "Z", "E"):
                self.config[f"{key.lower()}_mm_per_step"] = value
            elif key == "T":
                parts = value.split("/")
                if len(parts) == 5:
                    (self.config["s_machine_type"], self.config["s_x_max"],
                     self.config["s_y_max"], self.config["s_z_max"], _extra) = parts
            elif key == "U":
                self.encoding = value.replace("'", "") or "utf-8"
        try:
            fw = self.request("M4002", retries=2).strip()
            self.config["firmware"] = fw.split("ok ", 1)[-1] if "ok " in fw else fw
        except QidiError:
            self.config["firmware"] = "unknown"
        return self.config

    @staticmethod
    def frame(data, seek):
        """payload + 4-byte little-endian offset + XOR checksum + 0x83."""
        n = len(data)
        buf = bytearray(data) + bytearray(6)
        buf[n:n + 4] = struct.pack("<I", seek)
        checksum = 0
        for i in range(n + 4):
            checksum ^= buf[i]
        buf[n + 4] = checksum
        buf[n + 5] = BLOCK_TERMINATOR
        return bytes(buf)

    def upload(self, path, remote_name, progress=True):
        size = os.path.getsize(path)
        if size == 0:
            raise QidiError(f"{path} is empty")

        reply = self.request(f"M28 {remote_name}")
        if "Error" in reply:
            raise QidiError(f"printer refused to create {remote_name}: {reply.strip()}")
        self.log(f"opened {remote_name} ({size} bytes to send)")

        sent = 0
        last_pct = -1
        with open(path, "rb") as fp:
            while True:
                seek = fp.tell()
                chunk = fp.read(BUFSIZE)
                if not chunk:
                    break
                reply = self.request(self.frame(chunk, seek))
                if "ok" in reply:
                    sent = seek + len(chunk)
                elif "resend" in reply:
                    match = re.search(r"resend (\d+)", reply)
                    if not match:
                        raise QidiError(f"bad resend reply: {reply.strip()}")
                    fp.seek(int(match.group(1)), 0)
                    continue
                else:
                    raise QidiError(f"block at offset {seek} rejected: {reply.strip()}")

                if progress and self.verbose:
                    pct = int(100 * sent / size)
                    if pct != last_pct:
                        last_pct = pct
                        print(f"\r  uploading {pct:3d}%", end="", file=sys.stderr, flush=True)
        if progress and self.verbose:
            print("", file=sys.stderr)

        reply = self.request(f"M29 {remote_name}")
        if "Error" in reply:
            raise QidiError(f"printer refused to close {remote_name}: {reply.strip()}")
        self.log(f"closed {remote_name}")
        return remote_name

    def start_print(self, remote_name):
        reply = self.request(f'M6030 ":{remote_name}" I1')
        if "Error" in reply:
            raise QidiError(f"could not start print: {reply.strip()}")
        return reply.strip()

    def status(self):
        return {
            "temps": self.request("M119").strip(),
            "progress": self.request("M27").strip(),
        }


def find_compressor(explicit=None):
    if explicit:
        return explicit if os.path.exists(explicit) else None
    for candidate in MAC_COMPRESSOR_PATHS:
        if os.path.exists(candidate):
            return candidate
    return None


def compress(tool, gcode_path, config, verbose=True):
    """Produce <gcode_path>.tz using QIDI's compressor. Returns path or None."""
    out_dir = os.path.dirname(os.path.abspath(gcode_path))
    tz_path = gcode_path + ".tz"
    if os.path.exists(tz_path):
        os.remove(tz_path)
    cmd = [
        tool, gcode_path,
        config.get("x_mm_per_step", "0.0"), config.get("y_mm_per_step", "0.0"),
        config.get("z_mm_per_step", "0.0"), config.get("e_mm_per_step", "0.0"),
        out_dir,
        config.get("s_x_max", "0.0"), config.get("s_y_max", "0.0"),
        config.get("s_z_max", "0.0"), config.get("s_machine_type", "0"),
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    except (OSError, subprocess.SubprocessError) as exc:
        if verbose:
            print(f"compression failed ({exc}); sending plain G-code", file=sys.stderr)
        return None
    return tz_path if os.path.exists(tz_path) else None


def sanitize(name):
    """ChiTu firmware is happiest with short plain-ASCII 8.3-ish names."""
    stem = os.path.splitext(os.path.basename(name))[0]
    stem = stem.encode("ascii", "ignore").decode("ascii")
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("_.") or "orca"
    return stem[:40]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gcode", nargs="?", help="G-code file (Orca appends this automatically)")
    ap.add_argument("--ip", required=True, help="printer IP address")
    ap.add_argument("--name", help="filename on the printer (default: derived from the G-code file)")
    ap.add_argument("--print", dest="do_print", action="store_true",
                    help="start printing immediately after upload")
    ap.add_argument("--compress", action="store_true",
                    help="pre-compress with QIDI's VC_compress_gcode (gives the screen a preview and time estimate)")
    ap.add_argument("--compress-tool", help="path to VC_compress_gcode_MAC")
    ap.add_argument("--status", action="store_true", help="just report printer status and exit")
    ap.add_argument("--quiet", action="store_true", help="suppress progress output")
    args = ap.parse_args()

    printer = QidiPrinter(args.ip, verbose=not args.quiet)
    try:
        config = printer.connect()
        if args.status:
            for key, value in {**config, **printer.status()}.items():
                print(f"{key}: {value}")
            return 0

        if not args.gcode:
            ap.error("a G-code file is required unless --status is given")
        if not os.path.exists(args.gcode):
            raise QidiError(f"no such file: {args.gcode}")

        # Orca exports to a temp file; the user-facing name is in the environment.
        source_name = os.environ.get("SLIC3R_PP_OUTPUT_NAME") or args.name or args.gcode
        stem = sanitize(args.name or source_name)

        send_path, remote_name = args.gcode, stem + ".gcode"
        if args.compress:
            tool = find_compressor(args.compress_tool)
            if not tool:
                printer.log("VC_compress_gcode not found; sending plain G-code")
            else:
                tz = compress(tool, args.gcode, config, verbose=not args.quiet)
                if tz:
                    send_path, remote_name = tz, stem + ".gcode.tz"

        printer.upload(send_path, remote_name)
        if args.do_print:
            printer.log(printer.start_print(remote_name))
            print(f"printing {remote_name}")
        else:
            print(f"uploaded {remote_name} (start it from the printer screen)")
        return 0
    except QidiError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        printer.close()


if __name__ == "__main__":
    sys.exit(main())

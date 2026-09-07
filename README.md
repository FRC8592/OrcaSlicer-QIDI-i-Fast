# QIDI i-Fast — OrcaSlicer profile

> **Status: scaffolding only.** No profiles have been generated yet. This README is a
> skeleton; the provenance tables below are filled in as each value is derived.
> See [`ifast-orca-profile-handoff.md`](ifast-orca-profile-handoff.md) for the spec and
> [`CLAUDE.md`](CLAUDE.md) for the recon already done.

An OrcaSlicer printer profile (machine + process + minimal filament) for the
**QIDI i-Fast**, a machine OrcaSlicer does not ship a profile for.

- Build volume 330 × 250 × 320 mm, dual extruder (multi-tool), heated chamber
- Legacy QIDI generation — Chitu board, Marlin-flavored G-code, **not** Klipper

## Installation (Linux)

_TBD — copy the JSONs into `~/.config/OrcaSlicer/user/default/{machine,process,filament}/`
and restart OrcaSlicer. Exact steps written once the profiles exist._

## Provenance

### Derived from

_TBD — which stock OrcaSlicer profile this inherits from._

### Values from QIDI's published profiles

_TBD._

### Values from the reference G-code

_TBD._

### Unverified values

See [`TODO.md`](TODO.md).

## Scope

Network printing is **not** configured. The i-Fast speaks a proprietary UDP protocol
OrcaSlicer does not support; G-code reaches it by USB stick.

## Attribution and license

The profiles here derive from OrcaSlicer's stock QIDI vendor profiles, which are
licensed **AGPL-3.0** and themselves derive from **Bambu Studio** and **PrusaSlicer**
upstream. That attribution chain is preserved: this repo is AGPL-3.0.

## First print

Single extruder, PLA, small model, supervised, chamber heater off. Get that clean
before trusting anything else in here.

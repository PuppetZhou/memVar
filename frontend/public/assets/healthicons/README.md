# Controlled Healthicons subset

This directory contains only the local SVGs used by memVar's 11 anatomical
display systems. The site never loads an icon from a Healthicons CDN or another
external runtime endpoint. The twelfth system, `other_non_anatomical`, has no
organ icon by design.

The source was verified from the official [Health Icons repository](https://github.com/resolvetosavelives/healthicons), commit `36887b268d2cb61f8d91622ad459bdf07910c2b0` (2026-07-28). Exact upstream file names,
paths, styles, and local paths are recorded in `manifest.json`; the original
names are also retained in `TISSUE_ICON_ASSETS`.

All selected icons have a matched upstream outline and filled 24 px SVG. The
component uses outline by default and the filled local file for selection; it
does not create artificial variants. Upstream describes these icons as
CC0/public-domain in its README. This file intentionally records provenance
while project-wide license handling remains centralized elsewhere.

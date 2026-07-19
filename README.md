# Project Pathfinder

A Genshin Impact damage calculator built to fill a gap: strategy tools for
non-meta teams. Most calculators and guides optimize for established meta
picks — Pathfinder is for players who want real, data-driven guidance on
the characters and teams they actually want to play, even if the internet
says "don't."

Named after Nicole, my favorite support character — her whole kit is about
guiding people toward hidden value and lifting up the team around her.
Felt right.

## Project Goals
- Build a fully data-driven damage calculator (JSON character/weapon/artifact
  data → Python calculation), not hardcoded per-character logic
- Eventually, integrate an AWS Bedrock-powered recommendation engine to suggest
  build strategies for user-selected characters
- Serve as a practical learning project for Python, data modeling, and (later)
  AWS/ML engineering concepts, alongside AWS certification study

## Versions

### v1 — Vertical Slice: Normal Attack, Single Talent Level
Proof of concept for the core architecture: character data lives in JSON,
Python functions load it, look up the relevant multiplier, and calculate
verified damage output.

- Character: Navia (Normal Attack only)
- Talent level: fixed at a single value (no per-level scaling yet)
- Confirmed: base damage formula + defense reduction formula, hand-verified
  against manual calculation
- Proves: the JSON → function chain works end to end for one character

### v2 — Per-Level Talent Scaling
*(coming soon)*
Talent multipliers restructured to store all levels (`multiplier_by_level`),
reflecting how talent scaling actually works in-game rather than a single
fixed value. Requires a two-step lookup (talent level → multiplier) instead
of a flat value.

## Architecture Notes
- **Character / Talent / Weapon / Artifact** are static reference data —
  game-defined values that rarely change.
- **Build** is not a saved, persistent object. It's a `compile_build()`
  function that loads referenced Character/Weapon/Artifact data fresh and
  assembles final stats on demand — with an optional feature to save a
  lightweight *reference* (not compiled stats) to disk if a user wants to
  revisit a specific configuration later.
- This follows a single-source-of-truth principle: fixing a typo in a
  character's base stats should never require updating multiple saved files.

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
Talent multipliers restructured to store all levels (`multiplier_by_level`),
reflecting how talent scaling actually works in-game rather than a single
fixed value. Requires a two-step lookup (talent level → multiplier) instead
of a flat value.

### v3 - Elemental Skill, Single Talent Level
Added Navia's Elemental Skill ("Ceremonial Crystalshot") to her JSON, including
the Crystal Shrapnel resource mechanic (stack-based shardshot count and damage
bonus). Base multiplier sourced directly from in-game data at talent level 10.

New calculation functions handle Skill's two-part scaling: a multiplicative
bonus from shardshot count, plus a separate additive DMG bonus for stacks
consumed beyond 3. Verified by hand across all 6 stack values (1–6).

### v4 — Skill/Burst Full Scaling, Build Compiler
Corrected the defense formula, expanded Navia's Elemental Skill to the full
talent level range, implemented her Elemental Burst from scratch, and built
the first working version of the build compiler.

**Added**
- Corrected the defense multiplier formula to match the community-verified 
  KQM/wiki formula, using enemy level rather than a flat enemy DEF value. 
  All previously verified damage numbers were re-verified against the 
  corrected formula.
- Expanded Navia's Elemental Skill to use the full talent level range (1-13) 
  instead of a single hardcoded level.
- Implemented Navia's Elemental Burst from scratch, including both the 
  instant Skill DMG component and the 3-hit Cannon Fire Support component 
  over its duration. Fully mapped and verified across the full talent level 
  range.
- Built the first working version of the build compiler: `aggregate_equipment()` 
  combines Weapon and Artifact data into one equipment profile, and 
  `calculate_final_stats()` combines that with Character base stats to 
  produce final compiled stats (HP, ATK, DEF, CRIT Rate, CRIT DMG, ER, and 
  elemental DMG bonuses).

**Known limitations**
- **ATK/DEF calculation discrepancy**: in-game verification against a real 
  build revealed that the build compiler's final ATK and DEF values don't 
  match in-game values. Root cause identified: Artifact flat stat 
  contributions are currently being included in the same bucket as 
  Character/Weapon flat stats before the percentage multiplier is applied, 
  when they should be added afterward instead, unscaled. Fix planned for v5.
- Shardshot hit-count granularity (partial-hit-count damage tables) is 
  intentionally not modeled, since this is a ceiling calculator assuming 
  optimal execution, not a hit-registration simulator.
- Surging Blade (Navia's Skill bonus to Normal Attack) remains out of scope 
  pending the elemental damage type system.
- Weapon and Artifact passives beyond flat/percent stat bonuses (set 
  bonuses, conditional effects) are not yet modeled.

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
- Final stat compilation splits contributions into two categories: flat 
  stats (summed directly) and percentage stats (summed separately, then 
  applied once as a multiplier) — but only for HP, ATK, and DEF, since 
  these are the only stats with both a flat and percent form in-game. All 
  other stats (CRIT Rate, CRIT DMG, Energy Recharge, elemental DMG bonus, 
  etc.) are purely additive. **Note**: as of v4, Artifact flat contributions 
  are incorrectly included in the pre-multiplier bucket rather than added 
  after — this is the known v4 limitation above, with a structural fix 
  planned for v5.

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

### v1.1 — Vertical Slice: Normal Attack, Single Talent Level
Proof of concept for the core architecture: character data lives in JSON,
Python functions load it, look up the relevant multiplier, and calculate
verified damage output.

- Character: Navia (Normal Attack only)
- Talent level: fixed at a single value (no per-level scaling yet)
- Confirmed: base damage formula + defense reduction formula, hand-verified
  against manual calculation
- Proves: the JSON → function chain works end to end for one character

### v1.2 — Per-Level Talent Scaling
Talent multipliers restructured to store all levels (`multiplier_by_level`),
reflecting how talent scaling actually works in-game rather than a single
fixed value. Requires a two-step lookup (talent level → multiplier) instead
of a flat value.

### v1.3 - Elemental Skill, Single Talent Level
Added Navia's Elemental Skill ("Ceremonial Crystalshot") to her JSON, including
the Crystal Shrapnel resource mechanic (stack-based shardshot count and damage
bonus). Base multiplier sourced directly from in-game data at talent level 10.

New calculation functions handle Skill's two-part scaling: a multiplicative
bonus from shardshot count, plus a separate additive DMG bonus for stacks
consumed beyond 3. Verified by hand across all 6 stack values (1–6).

### v1.4 — Skill/Burst Full Scaling, Build Compiler
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
  
### v1.5 — Elemental Damage System, Level Scaling, Build Compiler Fix Verified
Confirmed and closed out the v4 known issue with real in-game verification, then 
built a full elemental damage type system (bonus DMG, enemy RES) and ascension-tier 
level scaling — completing Navia's vertical slice.

**Added**
- Confirmed the v4 ATK/DEF discrepancy root cause and verified the fix in-game: 
  restructured the build compiler into three distinct functions (`aggregate_equipment()`, 
  `calculate_flat_stats()`, `calculate_final_stats()`) so Artifact flat stats are 
  correctly added after the percent multiplier, not before. DEF matched real in-game 
  values almost exactly; remaining ATK variance was fully explained by an unmodeled 
  set bonus, not a calculation error.
- Restructured Character/Weapon/Artifact JSON schema: separated `bonus_dmg_values` 
  (elemental and generic damage bonuses) from `base_stats` (flat/percent-eligible 
  stats only), since these follow different aggregation math. Added `elemental_dmg_type` 
  at the talent level (not character level) to correctly support characters whose 
  different talents — or even the same talent under different conditions — deal 
  different elemental damage types.
- Built a new Enemy JSON reference type, decoupled from character level, storing 
  per-element RES values as decimals for direct use in multiplier formulas.
- Implemented `get_res_multiplier()` using the community-verified RES multiplier 
  formula (`1 - RES` for the 0–75% range), chained alongside the existing defense 
  multiplier across all three of Navia's damage functions (Normal Attack, Skill, Burst).
- Added `calculate_bonus_stats()` to combine Character, Weapon, and Artifact elemental 
  DMG bonus contributions into one compiled total, threaded through to all damage 
  calculations via `compiled_stats`.
- Added ascension-tier level scaling: `base_stats_by_level` stores HP/ATK/DEF/CRIT DMG 
  at each of Navia's 9 ascension breakpoints (levels 20–100, including the Masterless 
  Stella Fortuna-gated 95/100 tiers). `get_base_stats_at_level()` and 
  `get_base_stat_list()` merge level-specific stats with flat, non-scaling stats 
  (CRIT Rate, ER, EM, etc.) into one compiled block, letting the calculator represent 
  lower-investment characters accurately rather than assuming max level.
- Added `set` and `weapon_type` fields to Weapon/Artifact JSON (currently unused, 
  laying groundwork for future set-bonus and weapon-type-restriction logic).

**Known limitations**
- Weapon/Artifact set bonuses and conditional passives (e.g., piece-count checks, 
  party-composition effects like Navia's Mutual Assistance Network) remain unbuilt. 
  These require infrastructure — party composition modeling, reaction tracking, and 
  duration/timing — that doesn't exist yet and represents the next major slice of work.
- Surging Blade (Navia's Skill bonus to Normal Attack) remains out of scope, now 
  unblocked by the elemental damage system but still dependent on the same 
  timing/duration infrastructure above.
- RES reduction/shred (negative RES, RES ≥ 75%) is not modeled — only the standard 
  0–75% RES interval is implemented.
  
## v2.0.0 — Modular Architecture, Buff Tracking System

Phase 2 begins here: the single-notebook prototype (v1.x) has been restructured 
into a proper multi-file Python project, and a real time-based buff-tracking 
system has been designed and verified for the first time.

### Added
- **Project restructured from one notebook into modular files**: `constants.py`, 
  `data_loader.py`, `damage_core.py` (character-agnostic damage math + Normal 
  Attack, since NA's structure is consistent across characters), `build_compiler.py` 
  (Character/Weapon/Artifact aggregation), `buff_system.py` (new), and a 
  `characters/` package holding character-specific Skill/Burst logic.
- Renamed several functions to accurately reflect that they're character-specific, 
  not generic (`calculate_skill_damage` → `calculate_navia_skill_damage`, 
  `calculate_burst_damage` → `calculate_navia_burst_damage`, and their supporting 
  functions), since Skill/Burst mechanics genuinely differ per character while 
  Normal Attack's structure doesn't.
- `get_normal_attack_frame_events()` (renamed from `frame_counter()`): walks a 
  character's Normal Attack combo and returns a frame-indexed timeline of every 
  hit's damage — the first function in the project to answer "when," not just 
  "how much." Fully verified against Navia's real, community-sourced frame data 
  (hitmark, next-attack-available frame) across all 6 hits in her combo.
- Built Nicole's Elemental Skill: a one-time AoE damage hit plus Grace of Kenosis, 
  a capped ATK buff (`min(ratio × Nicole's ATK, level-specific max)`) granted to 
  the whole party.
- **New buff-tracking system**: `is_buff_active()` determines whether a buff 
  instance is active at a given frame (inclusive start, exclusive end); 
  `get_active_buff_totals()` collects all currently-active buffs from a list of 
  instances into one `{stat: value}` dict. `calculate_final_stats()` now accepts 
  an `active_buffs` parameter, correctly applied in the same "added after the 
  percent multiplier, unscaled" category as Artifact flat stats — verified with 
  a real end-to-end test showing Navia's Skill damage correctly increasing when 
  Grace of Kenosis is active.

### Known limitations
- **The conductor is not yet built.** This is the next major piece of work: 
  a function that walks an ordered rotation (e.g. Nicole's Skill → Navia's 
  Burst → Navia's Skill → Navia's Normal Attack combo), tracks a running 
  frame count across the entire sequence, creates buff instances when a 
  triggering action occurs (like casting Nicole's Skill), and checks them 
  against `is_buff_active()`/`get_active_buff_totals()` at each subsequent 
  hit — allowing a full team rotation's real DPS to be modeled, including 
  the exact timing windows where a buff from one character affects another 
  character's damage. The buff-tracking system (`is_buff_active`, 
  `get_active_buff_totals`, and `calculate_final_stats()`'s new 
  `active_buffs` parameter) is fully verified in isolation — this is the 
  proven foundation the conductor will be built on top of, not yet the 
  conductor itself.
- Frame data (hitmark/cancel timing) only exists for Navia; Linnea, 
  Columbina, and Nicole's Normal Attacks aren't tracked in the community's 
  frame data (their competitive builds don't rely on Normal Attack), and 
  Nicole is too recently released for frame data to exist anywhere yet.
- Nicole's Guidance of Theosis upgrade path (Ascension/Constellation-gated 
  enhancements to Grace of Kenosis) is deliberately out of scope — requires 
  party-composition modeling, continuous-on-field-time tracking, and 
  event-triggered re-buffing, none of which exist yet.
  
## v2.1.0 — Conductor v1: First Working Rotation

The conductor exists and works. This version answers the question Pathfinder 
was built to answer: a real, buff-aware, frame-timed multi-character rotation 
number, produced end-to-end from real build data.

### Added
- **`run_conductor()`**: walks an ordered rotation of action names, tracks a 
  single global frame timeline, checks/applies currently-active buffs before 
  each action (via `is_buff_active()`/`get_active_buff_totals()`, built last 
  session), and registers any buff an action creates — stamped with its true 
  global start frame (`current global frame + the buff's own hitmark offset`, 
  not just the action's start) so buffs that trigger partway through an 
  animation will be handled correctly once per-hit precision exists.
- **Registry pattern**: actions are looked up by name (`"nicole_skill"`, 
  `"navia_skill"`) against a dict mapping each to its function, owning 
  character, and talent type — the conductor itself has zero built-in 
  knowledge of any specific character or talent, keeping it fully generic 
  and requiring no changes as new characters/actions are added.
- **`apply_buffs_to_stats()`** (`build_compiler.py`): applies a dict of 
  currently-active flat buffs onto a character's static `compiled_stats`, 
  returning a new dict without ever mutating the original — `party` always 
  stores the clean, buff-free baseline.
- **Consistent action-return shape**: every registered action now returns 
  `{"damage": ..., "buff_created": {...} or None}`. Added `navia_skill_wrapper()` 
  and `nicole_skill_wrapper()` to give `calculate_navia_skill_damage()` and 
  Nicole's Skill this consistent shape without modifying the original 
  functions — Nicole's wrapper composes her damage and Grace of Kenosis buff 
  calculations (previously two separate function calls) into one action, 
  since casting her Skill is genuinely one action that does two things.
- **Real `main.py`**: compiles Navia's full build (Character + Weapon + 5 
  Artifacts), runs the conductor against a real two-action rotation 
  (`nicole_skill` → `navia_skill`), and produces a verified, correct total 
  rotation damage number. Verified against hand-math: buffed vs. unbuffed 
  Skill damage ratio matched the expected ATK increase ratio exactly.
- Added `action_frames` (time a character is occupied by an action, in 
  frames) to Navia's and Nicole's Elemental Skill data — Navia's sourced 
  from real KQM frame data (N1 cancel-window frame), Nicole's estimated 
  from community video timing (~30-40f midpoint), pending real frame data.
- Captured full Skill/Burst data (multiplier tables, mechanics, duration/CD) 
  for Linnea and Columbina — not yet wired into functions.

### Known limitations
- Buff `start_frame` currently uses each action's own start (or a hardcoded 
  hitmark of 0, accurate for Grace of Kenosis specifically) rather than 
  true per-hit precision, since Skill/Burst functions don't yet report 
  internal frame-indexed events the way `get_normal_attack_frame_events()` 
  does for Normal Attack. This is architecturally ready to extend — no 
  redesign needed, just applying the same pattern already proven there.
- Nicole's Burst, and Linnea's/Columbina's Skill and Burst, are data-captured 
  but not yet built into functions or wired into the registry.
- `action_frames` is missing for every talent except Navia's and Nicole's 
  Elemental Skill — needed before the conductor can run a full rotation 
  across all four characters.
- Nicole's compiled_stats in `main.py` is a placeholder (no real 
  weapon/artifact JSON files exist for her yet).
- Reactions (Lunar-Crystallize, etc.) remain out of scope; Linnea's and 
  Columbina's Skill data is captured as base-element (Geo/Hydro) with 
  reaction-type overrides deferred to future function logic.
  
## v2.2.0 — Stateful Mechanics & Elemental Reaction System Foundation

Built the project's first real class-based state tracking, then used that 
foundation to build a solid core of the elemental reaction system — one of 
the most mechanically dense systems in the game — including real Aura Tax, 
decay math, and category-specific damage formulas for four reaction 
categories, all verified against hand-calculated values. Several 
significant reaction types (Swirl's full complexity, Bloom family, 
Shattered) remain open, captured honestly in Known Limitations below.

### Added
- **`CrystalShrapnel` class** (`characters/navia.py`): Navia's first stateful 
  resource — tracks current stacks (capped at 6), with a combined 
  `consume_stacks()` that reads and resets atomically, since the real 
  mechanic (firing Skill) always does both together. Fully wired into 
  `navia_skill_wrapper()` and the conductor via a new `party[character]["unique_mechanics"]` 
  pattern — a generic, per-character dict for any stateful mechanic, so the 
  conductor's context-building code never needs character-specific branching 
  as new characters are added.
- **`ElementalAura` class** (new): the project's first enemy-side persistent 
  state, tracking every currently-applied element as a list of entries 
  (element, gauge units, decay duration, timestamp).
  - `apply_element()`: correctly applies the 20% Aura Tax on creation and on 
    refresh, uses "higher gauge wins" for refreshes, and inherits decay rate 
    from the original application — **except Pyro**, which uniquely replaces 
    its decay rate whenever a refresh actually wins, verified as a real, 
    documented exception (not modeled as a general rule).
  - `get_current_gauge()`: calculates real-time decay using the verified 
    formula `Current Gauge(t) = 0.8x × (1 - t/Base Duration)`, confirmed 
    against hand-calculated values at t=0, halfway, and full decay.
  - `get_elemental_reactions()`: identifies which reaction (if any) occurs 
    when a new element meets existing auras, correctly routing across four 
    distinct category shapes — Geo-triggered (one-directional), 
    Anemo/Swirl-triggered (one-directional), Amplifying (Vaporize/Melt — 
    order-sensitive, different multiplier depending on which element 
    triggers), and Other (order-independent: Overloaded, Superconduct, 
    Electro-Charged, Frozen, Burning).
- **`apply_amplifying_reaction()`** (`damage_core.py`): applies Vaporize/Melt's 
  multiplier (1.5x/2.0x depending on trigger direction) to a hit's existing 
  damage.
- **`apply_transformative_reaction()`** (`damage_core.py`): calculates 
  Overloaded/Superconduct/Electro-Charged damage using the real formula 
  (level-scaled base × EM bonus × RES), confirmed against the 5.2 patch's 
  updated multipliers and verified with hand-calculated EM-scaling checks.
- **`REACTION_LEVEL_MULTIPLIERS`**: full 9-point (ascension-level) table for 
  all 8 reaction damage types, sourced directly from the wiki's level-scaling 
  page.
- **Party composition checks**: `party_has_lunar_enabler()` and 
  `party_has_stellar_enabler()`, checking each character's new `vision_type` 
  field — groundwork for routing Geo+Hydro to Lunar-Crystallize (instead of 
  plain Crystallize) when a Moonwheel-vision character is present.

### Known limitations
- **Swirl** is more complex than initially scoped: damage differs by element 
  (Hydro only damages the original target; Pyro/Electro/Cryo spread AoE 
  damage to every enemy hit), requires a multi-enemy model that doesn't 
  exist yet, and Double Swirl (two simultaneous swirls from one hit) is 
  undocumented in code. Deferred.
- **Bloom/Burgeon/Hyperbloom** require a persistent "Dendro Core" object 
  (data captured in `REACTION_LEVEL_MULTIPLIERS`, no class built yet).
- **Shattered** isn't a reaction pair lookup at all — it's a conditional 
  check (Geo damage or Claymore heavy attack) layered on an existing Frozen 
  aura. Not yet implemented.
- **Lunar/Stellar reaction routing** isn't wired in yet — `party_has_lunar_enabler()`/
  `party_has_stellar_enabler()` exist, but `get_elemental_reactions()` still 
  always uses the plain (non-Lunar) Geo table regardless of party composition.
- **Lumi (Linnea) and Gravity Interference (Columbina)** — both are now 
  understood to require the same class-based, stateful pattern proven 
  tonight with `CrystalShrapnel` and `ElementalAura`, but neither has been 
  built yet.
- Tie-breaking behavior when two applications have exactly equal gauge 
  values is inferred (treated as no-change), not explicitly documented — 
  judged practically irrelevant given how unlikely simultaneous-frame ties 
  are in real play.

## Architecture Notes
- Final stat compilation now happens across four distinct functions, each with a 
  single responsibility: `aggregate_equipment()` (combine Weapon + Artifacts), 
  `calculate_flat_stats()` (Character + Weapon flat stats, HP/ATK/DEF percent formula), 
  `calculate_bonus_stats()` (elemental DMG bonus aggregation across all sources), 
  `calculate_final_stats()` (final assembly). This resolved the v4 known issue: 
  Artifact flat contributions are correctly added *after* the percent multiplier is 
  applied to Character + Weapon's flat total, not folded into the same pre-multiplier 
  bucket.
- Elemental damage type lives at the talent level, not the character level, since a 
  single character's talents (and even a single talent, conditionally) can deal 
  different elemental types.
- Buffs are never baked into `compiled_stats` at compile time — that dict 
  represents a character's static, gear-based build and stays time-independent. 
  Instead, buffs are checked fresh against the current frame each time a 
  damage calculation runs, and their contribution is passed into 
  `calculate_final_stats()` per-call via `active_buffs`. This mirrors how 
  Artifact flat stats are added after the percent multiplier, unscaled — 
  buffs follow the same category, just re-evaluated per hit instead of 
  computed once.
  - The conductor is intentionally "dumb" by design: it only knows how to
  sequence actions and track time. It has no built-in knowledge of any 
  character or talent type — that knowledge lives entirely in the registry 
  (which action maps to which function/character/talent_type) and in each 
  action's own wrapper function. Adding a new character or action requires 
  zero changes to `conductor.py` itself.
- Character-specific persistent state (Crystal Shrapnel, and future 
  mechanics like Lumi) lives in `party[character]["unique_mechanics"]`, a 
  per-character dict of arbitrary objects. The conductor always offers this 
  key generically (`party[character].get("unique_mechanics", {})`) regardless 
  of whether a character has one — new characters with unique state never 
  require conductor changes, only an addition to their own `party` entry and 
  wrapper function.
- Enemy elemental state now has a real home: `ElementalAura`, separate from 
  the static `resistances` dict already on Enemy JSON. This mirrors the 
  Character/Build separation from early in the project — static reference 
  data (resistances) vs. compute-on-demand, time-dependent state (auras).

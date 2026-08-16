from constants import TEST_ENEMY_LEVEL, TEST_CHARACTER_LEVEL
from data_loader import load_json
from build_compiler import (
    get_base_stats_at_level,
    get_base_stat_list,
    get_percent_stats_at_level,
    aggregate_equipment,
    calculate_flat_stats,
    calculate_bonus_stats,
    calculate_final_stats,
)
from characters.navia import navia_skill_wrapper
from characters.nicole import nicole_skill_wrapper
from conductor import run_conductor


def compile_character(character_file, weapon_file, artifact_files):
    # Runs the full build-compiler chain for one character: Character +
    # Weapon + Artifacts -> one static, buff-free compiled_stats dict.
    character_data = load_json(character_file)
    weapon_data = load_json(weapon_file)
    equipment_list = [load_json(f) for f in artifact_files]

    build_data = aggregate_equipment(equipment_list)
    level_stat = get_base_stats_at_level(character_data, TEST_CHARACTER_LEVEL)
    base_stats = get_base_stat_list(character_data, level_stat)
    level_percent = get_percent_stats_at_level(character_data, TEST_CHARACTER_LEVEL)
    flat_totals = calculate_flat_stats(base_stats, build_data, weapon_data, level_percent)
    bonus_totals = calculate_bonus_stats(character_data, build_data, weapon_data)
    compiled_stats = calculate_final_stats(build_data, flat_totals, bonus_totals, active_buffs={})

    return character_data, compiled_stats


# ------------------------------------------------------------------
# Compile Navia's real build
# ------------------------------------------------------------------
navia_data, navia_compiled_stats = compile_character(
    character_file="naviav5.json",
    weapon_file="verdictv2.json",
    artifact_files=[
        "selfless_floral_accessory.json",
        "honest_quill.json",
        "faithful_hourglass.json",
        "a_horn_unwindedv2.json",
        "compassionate_ladies_hat.json",
    ],
)
print("Navia compiled_stats:", navia_compiled_stats)

# ------------------------------------------------------------------
# Compile Nicole's build.
# NOTE: Nicole doesn't have real weapon/artifact JSON files built yet
# (known gap — see project notes). Using a placeholder compiled_stats
# with a round ATK value instead of the full compile chain, same as the
# earlier Grace of Kenosis verification test. Swap this out for a real
# compile_character() call once her gear JSONs exist.
# ------------------------------------------------------------------
nicole_data = load_json("nicole.json")
nicole_compiled_stats = {
    "atk": 2000, "max_hp": 10000, "def": 800,
    "crit_rate": 50, "crit_dmg": 100, "energy_recharge": 100,
    "cd_reduction": 0, "shield_strength": 0,
    "pyro": 0, "hydro": 0, "dendro": 0, "electro": 0,
    "anemo": 0, "cryo": 0, "geo": 0, "physical": 0, "other": 0,
}
print("Nicole compiled_stats (PLACEHOLDER — real gear not built yet):", nicole_compiled_stats)

# ------------------------------------------------------------------
# Enemy
# ------------------------------------------------------------------
enemy_data = load_json("testdummy.json")

# ------------------------------------------------------------------
# Party, registry, rotation
# ------------------------------------------------------------------
party = {
    "navia": {"character_data": navia_data, "compiled_stats": navia_compiled_stats},
    "nicole": {"character_data": nicole_data, "compiled_stats": nicole_compiled_stats},
}

registry = {
    "nicole_skill": {"function": nicole_skill_wrapper, "character": "nicole", "talent_type": "elemental_skill"},
    "navia_skill": {"function": navia_skill_wrapper, "character": "navia", "talent_type": "elemental_skill"},
}

rotation = ["nicole_skill", "navia_skill"]

# ------------------------------------------------------------------
# Run the conductor — this is the actual answer the project set out
# to produce: a real, buff-aware, frame-timed team rotation result.
# ------------------------------------------------------------------
results = run_conductor(
    registry=registry,
    rotation=rotation,
    party=party,
    enemy_data=enemy_data,
    enemy_level=TEST_ENEMY_LEVEL,
    character_level=TEST_CHARACTER_LEVEL,
)

print()
print("=== Conductor Results ===")
for frame, result in results.items():
    print(f"Frame {frame}: {result}")

total_damage = sum(result["damage"] for result in results.values())
print()
print("Total rotation damage:", total_damage)

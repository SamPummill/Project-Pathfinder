from constants import TEST_ENEMY_LEVEL, TEST_CHARACTER_LEVEL
from data_loader import load_json
from damage_core import get_normal_attack_frame_events, calculate_hit_damage
from build_compiler import (
    get_base_stats_at_level,
    get_base_stat_list,
    get_percent_stats_at_level,
    aggregate_equipment,
    calculate_flat_stats,
    calculate_bonus_stats,
    calculate_final_stats,
)
from buff_system import get_active_buff_totals
from characters.navia import (
    calculate_navia_skill_damage,
    calculate_navia_burst_damage,
)
from characters.nicole import get_nicole_skill_buff

# ------------------------------------------------------------------
# Compile Navia's build (Character + Weapon + 5 Artifacts)
# ------------------------------------------------------------------
character_data = load_json("naviav5.json")
weapon_data = load_json("verdictv2.json")
flower_data = load_json("selfless_floral_accessory.json")
feather_data = load_json("honest_quill.json")
sands_data = load_json("faithful_hourglass.json")
goblet_data = load_json("a_horn_unwindedv2.json")
circlet_data = load_json("compassionate_ladies_hat.json")
enemy_data = load_json("testdummy.json")

equipment_list = [flower_data, feather_data, sands_data, goblet_data, circlet_data]
build_data = aggregate_equipment(equipment_list)
level_stat = get_base_stats_at_level(character_data, TEST_CHARACTER_LEVEL)
base_stats = get_base_stat_list(character_data, level_stat)
level_percent = get_percent_stats_at_level(character_data, TEST_CHARACTER_LEVEL)
flat_totals = calculate_flat_stats(base_stats, build_data, weapon_data, level_percent)
bonus_totals = calculate_bonus_stats(character_data, build_data, weapon_data)

# BUG FIX: calculate_final_stats() now takes active_buffs. Passing {} here
# means "no buffs active" — same as before this parameter existed.
compiled_stats = calculate_final_stats(build_data, flat_totals, bonus_totals, active_buffs={})
print("Navia compiled_stats:", compiled_stats)

# ------------------------------------------------------------------
# Navia's Normal Attack — single hit, full combo total, and the
# frame-indexed event timeline
# ------------------------------------------------------------------
single_hit = calculate_hit_damage(
    character_data=character_data,
    compiled_stats=compiled_stats,
    hit_number="1",
    talent_level=1,
    enemy_level=TEST_ENEMY_LEVEL,
    character_level=TEST_CHARACTER_LEVEL,
    enemy_data=enemy_data,
)
print("Single hit (N1, level 1):", single_hit)

frame_events = get_normal_attack_frame_events(
    character_data=character_data,
    compiled_stats=compiled_stats,
    enemy_level=TEST_ENEMY_LEVEL,
    character_level=TEST_CHARACTER_LEVEL,
    talent_level=10,
    enemy_data=enemy_data,
)
print("Frame-indexed NA combo:", frame_events)

# ------------------------------------------------------------------
# Navia's Skill and Burst
# ------------------------------------------------------------------
skill_result = calculate_navia_skill_damage(
    character_data=character_data,
    crystal_shrapnel_stacks=6,
    talent_level=13,
    enemy_level=TEST_ENEMY_LEVEL,
    character_level=TEST_CHARACTER_LEVEL,
    compiled_stats=compiled_stats,
    enemy_data=enemy_data,
)
print("Navia Skill damage:", skill_result)

burst_result = calculate_navia_burst_damage(
    character_data=character_data,
    talent_level=13,
    enemy_level=TEST_ENEMY_LEVEL,
    character_level=TEST_CHARACTER_LEVEL,
    compiled_stats=compiled_stats,
    enemy_data=enemy_data,
)
print("Navia Burst damage:", burst_result)

# ------------------------------------------------------------------
# Nicole's Grace of Kenosis buff — quick sanity check with hardcoded
# ATK values (matches the low/high cap test from tonight's session)
# ------------------------------------------------------------------
nicole_data = load_json("nicole.json")
nicole_compiled_stats_low = {"atk": 1000}
nicole_compiled_stats_high = {"atk": 10000}
low_bonus = get_nicole_skill_buff(character_data=nicole_data, talent_level=10, compiled_stats=nicole_compiled_stats_low)
high_bonus = get_nicole_skill_buff(character_data=nicole_data, talent_level=10, compiled_stats=nicole_compiled_stats_high)
print("Grace of Kenosis (under cap):", low_bonus)
print("Grace of Kenosis (over cap, clamped):", high_bonus)

# ------------------------------------------------------------------
# Buff system — is a buff active at a given frame, and applying an
# active buff into a real damage calculation via calculate_final_stats()
# ------------------------------------------------------------------
buff_instance = {"stat": "atk", "bonus_type": "flat", "value": low_bonus, "start_frame": 200, "duration": 1200}
buff_instances = [buff_instance]

active_buffs_at_500 = get_active_buff_totals(buff_instances=buff_instances, current_frame=500)
print("Active buffs at frame 500:", active_buffs_at_500)

# BUG FIX: this call was also missing active_buffs before tonight's change.
buffed_compiled_stats = calculate_final_stats(build_data, flat_totals, bonus_totals, active_buffs=active_buffs_at_500)
print("Navia compiled_stats WITH Grace of Kenosis active:", buffed_compiled_stats)

buffed_skill_result = calculate_navia_skill_damage(
    character_data=character_data,
    crystal_shrapnel_stacks=6,
    talent_level=13,
    enemy_level=TEST_ENEMY_LEVEL,
    character_level=TEST_CHARACTER_LEVEL,
    compiled_stats=buffed_compiled_stats,
    enemy_data=enemy_data,
)
print("Navia Skill damage WITH Grace of Kenosis:", buffed_skill_result)

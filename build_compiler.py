def get_base_stats_at_level(character_data, character_level):
    base_stats_by_level = character_data["base_stats_by_level"]
    level_key = str(character_level)
    level_stat = base_stats_by_level[level_key]
    return level_stat


def get_base_stat_list(character_data, level_stat):
    base_stats = character_data["base_stats"].copy()
    base_stats.update(level_stat)
    return base_stats


def get_percent_stats_at_level(character_data, character_level):
    percent_stats_by_level = character_data["percent_stats_by_level"]
    level_key = str(character_level)
    level_percent = percent_stats_by_level.get(level_key, {})
    return level_percent


def aggregate_equipment(equipment_list):
    # combines Weapon + all Artifact pieces (NOT Character) into one equipment profile
    build_flat_totals = {}
    build_percent_totals = {}
    build_bonus_dmg_totals = {}
    for equipment in equipment_list:
        flat_stats = equipment["flat_stat_values"]
        for stat_name in flat_stats:
            build_flat_totals[stat_name] = build_flat_totals.get(stat_name, 0) + flat_stats[stat_name]
        percent_values = equipment["percent_stat_values"]
        for stat_name in percent_values:
            build_percent_totals[stat_name] = build_percent_totals.get(stat_name, 0) + percent_values[stat_name]
        bonus_dmg_totals = equipment["bonus_dmg_values"]
        for bonus_dmg_name in bonus_dmg_totals:
            build_bonus_dmg_totals[bonus_dmg_name] = build_bonus_dmg_totals.get(bonus_dmg_name, 0) + bonus_dmg_totals[bonus_dmg_name]
    build_total = {
        "flat_stat_values": build_flat_totals,
        "percent_stat_values": build_percent_totals,
        "bonus_dmg_values": build_bonus_dmg_totals,
    }
    return build_total


def calculate_flat_stats(base_stats, build_total, weapon_data, level_percent):
    # combines Character (base_stats, already merged with level-scaling) + Weapon
    # flat stats, then applies the HP/ATK/DEF flat-times-percent formula.
    # level_percent covers ascension-tied percent stats (e.g. Nicole's ATK%).
    base_character_stats = base_stats
    weapon_totals = weapon_data["flat_stat_values"]
    flat_totals = {}
    for base_character_stat in base_character_stats:
        base_stat = base_character_stats[base_character_stat]
        weapon_stat = weapon_totals[base_character_stat]
        flat_stat = base_stat + weapon_stat
        flat_totals[base_character_stat] = flat_stat
    flat_max_hp_stat = flat_totals["max_hp"]
    flat_atk_stat = flat_totals["atk"]
    flat_def_stat = flat_totals["def"]
    percent_max_hp_increase = (
        weapon_data["percent_stat_values"].get("max_hp", 0)
        + build_total["percent_stat_values"].get("max_hp", 0)
        + level_percent.get("max_hp", 0)
    )
    percent_atk_increase = (
        weapon_data["percent_stat_values"].get("atk", 0)
        + build_total["percent_stat_values"].get("atk", 0)
        + level_percent.get("atk", 0)
    )
    percent_def_increase = (
        weapon_data["percent_stat_values"].get("def", 0)
        + build_total["percent_stat_values"].get("def", 0)
        + level_percent.get("def", 0)
    )
    final_max_hp_value = flat_max_hp_stat * (percent_max_hp_increase + 1)
    final_atk_value = flat_atk_stat * (percent_atk_increase + 1)
    final_def_value = flat_def_stat * (percent_def_increase + 1)
    flat_totals["max_hp"] = final_max_hp_value
    flat_totals["atk"] = final_atk_value
    flat_totals["def"] = final_def_value
    return flat_totals


def calculate_bonus_stats(character_data, build_total, weapon_data):
    # combines Character + Weapon + Artifact elemental DMG bonus contributions
    character_bonus_stats = character_data["bonus_dmg_values"]
    weapon_bonus_stats = weapon_data["bonus_dmg_values"]
    build_bonus_stats = build_total["bonus_dmg_values"]
    bonus_totals = {}
    for bonus_stat in character_bonus_stats:
        character_stat = character_bonus_stats[bonus_stat]
        weapon_stat = weapon_bonus_stats[bonus_stat]
        build_stat = build_bonus_stats[bonus_stat]
        bonus_stats = character_stat + weapon_stat + build_stat
        bonus_totals[bonus_stat] = bonus_stats
    return bonus_totals


def calculate_final_stats(build_total, flat_totals, bonus_totals, active_buffs=None):
    # final assembly: Artifact flat stats (unscaled) + currently-active buffs
    # (also unscaled, since is_buff_active/get_active_buff_totals already resolved
    # them to flat, ready-to-add numbers) get added on top of the already-computed
    # flat_totals, then elemental bonus values get merged in.
    # active_buffs defaults to an empty dict (no buffs) if the caller doesn't
    # pass one, so this stays safe to call the same way it always has been.
    if active_buffs is None:
        active_buffs = {}
    build_totals = build_total["flat_stat_values"]
    stat_total = {}
    for total in build_totals:
        build_stat = build_totals[total]
        buff_stats = active_buffs.get(total, 0)
        stat_total[total] = flat_totals[total] + build_stat + buff_stats
    stat_total.update(bonus_totals)
    return stat_total


def apply_buffs_to_stats(compiled_stats, buffs):
    # Takes an already-finished, STATIC compiled_stats dict (the kind stored
    # in `party`) and a small {stat: value} dict of currently-active buffs
    # (the output of get_active_buff_totals()), and returns a NEW dict with
    # those buffs added on top — never mutating the original compiled_stats,
    # so the static baseline stored in `party` stays clean and reusable for
    # every future action, regardless of what's active right now.
    copied_stats = compiled_stats.copy()
    for stat in buffs:
        copied_stats[stat] = copied_stats[stat] + buffs[stat]
    return copied_stats

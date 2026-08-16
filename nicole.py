from damage_core import calculate_base_damage, apply_defense_multiplier, apply_res_multiplier


def get_nicole_skill_buff(character_data, talent_level, compiled_stats, **kwargs):
    # Grace of Kenosis: a flat ATK bonus equal to a ratio of Nicole's own
    # compiled ATK, capped at a level-specific maximum. This bonus is a flat,
    # pre-computed number meant to be applied AFTER the recipient's own
    # flat-times-percent formula (same category as an Artifact's flat stats),
    # not summed into the recipient's percent bucket.
    bonus_ratio_by_level = character_data["talents"]["elemental_skill"]["grace_of_kenosis"]["atk_bonus_ratio_by_level"]
    ratio_key = str(talent_level)
    base_ratio = bonus_ratio_by_level[ratio_key]
    atk_bonus = base_ratio * compiled_stats["atk"]
    max_bonus_by_level = character_data["talents"]["elemental_skill"]["grace_of_kenosis"]["atk_bonus_max_by_level"]
    max_key = str(talent_level)
    max_value = max_bonus_by_level[max_key]
    result = min(atk_bonus, max_value)
    return result


def get_nicole_skill_dmg(character_data, talent_level, compiled_stats, enemy_level, character_level, enemy_data, **kwargs):
    # Nicole's Skill also deals a one-time AoE Pyro hit on cast, separate
    # from the Grace of Kenosis buff
    scaling_stat_name = character_data["talents"]["elemental_skill"]["scaling_stat"]
    scaling_stat_value = compiled_stats[scaling_stat_name]

    skill_multiplier = character_data["talents"]["elemental_skill"]["skill_dmg_by_level"][str(talent_level)]

    elemental_bonus = character_data["talents"]["elemental_skill"]["elemental_dmg_type"]
    elemental_dmg_value = compiled_stats[elemental_bonus]
    other_dmg_value = compiled_stats.get("other", 0)
    bonus_dmg = elemental_dmg_value + other_dmg_value
    skill_base_damage = calculate_base_damage(skill_multiplier, scaling_stat_value)
    skill_dmg = skill_base_damage * (bonus_dmg + 1)
    skill_defense_applied = apply_defense_multiplier(skill_dmg, enemy_level, character_level)
    skill_final = apply_res_multiplier(enemy_data, elemental_bonus, skill_defense_applied)
    return skill_final


def nicole_skill_wrapper(character_data, compiled_stats, talent_level, enemy_level, character_level, enemy_data, **kwargs):
    # Casting Nicole's Skill is ONE action that does TWO things: deals a
    # one-time AoE hit, and creates the Grace of Kenosis buff. This wrapper
    # composes the two already-independent, already-tested functions above
    # into one registry-ready action, returning a consistent shape the
    # conductor can read: {"damage": ..., "buff_created": {...} or None}.
    #
    # Grace of Kenosis's mechanic-specific facts (it targets "atk", lasts
    # 1200 frames/20s, and triggers on cast — hitmark 0, not partway through
    # the animation) are hardcoded here since they're fixed, known truths
    # about this specific buff, not values that vary per-call.
    nicole_damage = get_nicole_skill_dmg(
        character_data=character_data,
        talent_level=talent_level,
        compiled_stats=compiled_stats,
        enemy_level=enemy_level,
        character_level=character_level,
        enemy_data=enemy_data,
    )
    nicole_buffs = get_nicole_skill_buff(
        character_data=character_data,
        talent_level=talent_level,
        compiled_stats=compiled_stats,
    )
    nicole_skill = {
        "damage": nicole_damage,
        "buff_created": {
            "stat": "atk",
            "value": nicole_buffs,
            "duration": 1200,
            "hitmark": 0,
        },
    }
    return nicole_skill

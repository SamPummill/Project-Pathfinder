def apply_defense_multiplier(damage, enemy_level, character_level):
    # calculate the defense multiplier using the KQM-verified formula
    def_multiplier = (character_level + 100) / ((character_level + 100) + (enemy_level + 100))
    return damage * def_multiplier


def apply_res_multiplier(enemy_data, elemental_dmg_type, damage):
    res_type = elemental_dmg_type
    res_value = enemy_data["resistances"][res_type]
    res_multiplier = 1 - res_value
    return damage * res_multiplier


def calculate_base_damage(multiplier, scaling_stat_value):
    # multiplier is a percentage (e.g. 93.52 for 93.52%) so it's divided by 100 first
    return (multiplier / 100) * scaling_stat_value


def get_normal_attack_multiplier(character_data, hit_number, talent_level):
    # get the multiplier for a specific hit of the normal attack at a given talent level
    hits = character_data["talents"]["normal_attack"]["hits"]
    for hit in hits:
        if hit["hit_number"] == hit_number:
            level_lookup = hit["multiplier_by_level"]
            level_key = str(talent_level)
            multiplier = level_lookup[level_key]
            return multiplier
    return None


def calculate_hit_damage(character_data, compiled_stats, hit_number, enemy_level, character_level, talent_level, enemy_data):
    # calculate the final damage of a specific hit of the normal attack —
    # works for any character, since normal_attack's structure (scaling_stat,
    # elemental_dmg_type, hits/multiplier_by_level) is consistent across characters
    multiplier = get_normal_attack_multiplier(character_data, hit_number, talent_level)
    scaling_stat_name = character_data["talents"]["normal_attack"]["scaling_stat"]
    scaling_stat_value = compiled_stats[scaling_stat_name]
    elemental_bonus = character_data["talents"]["normal_attack"]["elemental_dmg_type"]
    elemental_dmg_value = compiled_stats[elemental_bonus]
    other_dmg_value = compiled_stats.get("other", 0)
    bonus_dmg = elemental_dmg_value + other_dmg_value
    base_dmg = calculate_base_damage(multiplier, scaling_stat_value)
    normal_attack_dmg = base_dmg * (bonus_dmg + 1)
    defense_applied = apply_defense_multiplier(normal_attack_dmg, enemy_level, character_level)
    final = apply_res_multiplier(enemy_data, elemental_bonus, defense_applied)
    return final


def get_normal_attack_frame_events(character_data, compiled_stats, enemy_level, character_level, talent_level, enemy_data):
    # renamed from frame_counter() for clarity — walks a character's Normal Attack
    # combo and returns a dict keyed by absolute frame, each holding a list of
    # events ({"hit_number": ..., "damage": ...}) that land on that frame.
    # Works for any character with frame_data populated (currently only Navia).
    hits = character_data["talents"]["normal_attack"]["hits"]
    current_frame = 0
    results = {}
    for hit in hits:
        absolute_frame = current_frame + hit["frame_data"]["hitmark"]
        damage = calculate_hit_damage(
            character_data=character_data,
            compiled_stats=compiled_stats,
            hit_number=hit["hit_number"],
            talent_level=talent_level,
            enemy_level=enemy_level,
            character_level=character_level,
            enemy_data=enemy_data,
        )
        event = {"hit_number": hit["hit_number"], "damage": damage}
        frame_events = results.get(absolute_frame, [])
        frame_events.append(event)
        results[absolute_frame] = frame_events
        current_frame = current_frame + hit["frame_data"].get("next_na_frame", 0)
    return results

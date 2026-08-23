from damage_core import calculate_base_damage, apply_defense_multiplier, apply_res_multiplier


class CrystalShrapnel:
    def __init__(self, crystal_shrapnel_stacks=0):
        self.crystal_shrapnel_stacks = crystal_shrapnel_stacks

    def add_stack(self):
        self.crystal_shrapnel_stacks = min(self.crystal_shrapnel_stacks + 1, 6)
        
    def consume_stacks(self):
        stacks = self.crystal_shrapnel_stacks
        self.crystal_shrapnel_stacks = 0
        return stacks

def get_navia_elemental_skill_multiplier(character_data, crystal_shrapnel_stacks):
    # renamed from get_elemental_skill_multiplier — this is Navia's own
    # Crystal Shrapnel stack mechanic, not a generic Skill pattern
    stacks = character_data["talents"]["elemental_skill"]["stacks"]
    for stack in stacks:
        if stack["stacks_consumed"] == crystal_shrapnel_stacks:
            shardshots = stack["shardshots"]
            dmg_bonus = stack["dmg_bonus"]
            pct_of_base = stack["pct_of_base"]
            return shardshots, dmg_bonus, pct_of_base


def get_navia_elemental_skill_base_multiplier(character_data, talent_level):
    # renamed from get_elemental_skill_base_multiplier
    base_multiplier_by_level = character_data["talents"]["elemental_skill"]["base_multiplier_by_level"]
    multiplier_key = str(talent_level)
    base_multiplier = base_multiplier_by_level[multiplier_key]
    return base_multiplier

def calculate_navia_skill_damage(character_data, crystal_shrapnel_stacks, talent_level, enemy_level, character_level, compiled_stats, enemy_data, **kwargs):
    # renamed from calculate_skill_damage — Navia-specific due to the
    # shardshot-stack scaling mechanic
    base_multiplier = get_navia_elemental_skill_base_multiplier(character_data, talent_level)
    shardshots, dmg_bonus, pct_of_base = get_navia_elemental_skill_multiplier(character_data, crystal_shrapnel_stacks)

    scaled_multiplier = base_multiplier * (pct_of_base / 100)
    final_multiplier = scaled_multiplier * (1 + dmg_bonus / 100)

    scaling_stat_name = character_data["talents"]["elemental_skill"]["scaling_stat"]
    scaling_stat_value = compiled_stats[scaling_stat_name]

    elemental_bonus = character_data["talents"]["elemental_skill"]["elemental_dmg_type"]
    elemental_dmg_value = compiled_stats[elemental_bonus]
    other_dmg_value = compiled_stats.get("other", 0)
    bonus_dmg = elemental_dmg_value + other_dmg_value
    base_dmg = calculate_base_damage(final_multiplier, scaling_stat_value)
    elemental_skill_dmg = base_dmg * (bonus_dmg + 1)
    defense_applied = apply_defense_multiplier(elemental_skill_dmg, enemy_level, character_level)
    final = apply_res_multiplier(enemy_data, elemental_bonus, defense_applied)
    return final


def navia_skill_wrapper(character_data, navia_shrapnel, talent_level, enemy_level, character_level, compiled_stats, enemy_data, **kwargs):
    # calculate_navia_skill_damage() returns a raw number, not a dict — but
    # the conductor expects every registry action to return a consistent
    # {"damage": ..., "buff_created": ... or None} shape, since it always
    # calls result.get("buff_created", None) after every action regardless
    # of which character/talent it was. This thin wrapper supplies that
    # consistent shape without changing calculate_navia_skill_damage() at
    # all. Navia's Skill doesn't create any buff, so buff_created is None.
    damage = calculate_navia_skill_damage(
        character_data=character_data,
        crystal_shrapnel_stacks=navia_shrapnel.consume_stacks(),
        talent_level=talent_level,
        enemy_level=enemy_level,
        character_level=character_level,
        compiled_stats=compiled_stats,
        enemy_data=enemy_data,
    )
    return {"damage": damage, "buff_created": None}


def calculate_navia_burst_damage(character_data, talent_level, enemy_level, character_level, compiled_stats, enemy_data, **kwargs):
    # renamed from calculate_burst_damage — Navia-specific due to the
    # instant Skill DMG + 3-hit Cannon Fire Support dual-component structure
    scaling_stat_name = character_data["talents"]["elemental_burst"]["scaling_stat"]
    scaling_stat_value = compiled_stats[scaling_stat_name]

    skill_multiplier = character_data["talents"]["elemental_burst"]["skill_dmg_by_level"][str(talent_level)]
    cannon_multiplier = character_data["talents"]["elemental_burst"]["cannon_fire_support_dmg_by_level"][str(talent_level)]
    hit_count = character_data["talents"]["elemental_burst"]["cannon_fire_support_hit_count"]

    elemental_bonus = character_data["talents"]["elemental_burst"]["elemental_dmg_type"]
    elemental_dmg_value = compiled_stats[elemental_bonus]
    other_dmg_value = compiled_stats.get("other", 0)
    bonus_dmg = elemental_dmg_value + other_dmg_value

    skill_base_damage = calculate_base_damage(skill_multiplier, scaling_stat_value)
    skill_dmg = skill_base_damage * (bonus_dmg + 1)
    skill_defense_applied = apply_defense_multiplier(skill_dmg, enemy_level, character_level)
    skill_final = apply_res_multiplier(enemy_data, elemental_bonus, skill_defense_applied)

    cannon_base_damage = calculate_base_damage(cannon_multiplier, scaling_stat_value)
    cannon_dmg = cannon_base_damage * (bonus_dmg + 1)
    cannon_defense_applied_single_hit = apply_defense_multiplier(cannon_dmg, enemy_level, character_level)
    cannon_final_single_hit = apply_res_multiplier(enemy_data, elemental_bonus, cannon_defense_applied_single_hit)
    cannon_final_total = cannon_final_single_hit * hit_count

    total_damage = skill_final + cannon_final_total

    return total_damage, skill_final, cannon_final_single_hit, cannon_final_total

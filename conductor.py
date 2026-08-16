from buff_system import get_active_buff_totals
from build_compiler import apply_buffs_to_stats


def run_conductor(registry, rotation, party, enemy_data, enemy_level, character_level):
    # registry: {action_name: {"function": ..., "character": ..., "talent_type": ...}}
    # rotation: ordered list of action names, e.g. ["nicole_skill", "navia_skill"]
    # party: {character_name: {"character_data": ..., "compiled_stats": ...}}
    #   party stores each character's STATIC, buff-free compiled_stats.
    #   Buffs are never baked into party — they're applied fresh, per action,
    #   via apply_buffs_to_stats(), so party never goes stale.
    #
    # The conductor's job is strictly sequencing + timekeeping: it doesn't
    # know what a Skill or Burst IS, only how to look one up, call it with
    # a shared context, and track when things happened relative to one
    # global frame timeline. Every registry action must return a consistent
    # {"damage": ..., "buff_created": {...} or None} shape.
    global_frame_counter = 0
    action_results = {}
    buff_instances = []

    for action in rotation:
        function = registry[action]["function"]
        character = registry[action]["character"]
        talent_type = registry[action]["talent_type"]

        character_data = party[character]["character_data"]
        compiled_stats = party[character]["compiled_stats"]

        # Check which buffs are active RIGHT NOW, before this action runs,
        # using the global counter's current (pre-advance) value.
        buffs = get_active_buff_totals(buff_instances=buff_instances, current_frame=global_frame_counter)
        buffed_compiled_stats = apply_buffs_to_stats(compiled_stats=compiled_stats, buffs=buffs)

        context = {
            "character_data": character_data,
            "compiled_stats": buffed_compiled_stats,
            "enemy_data": enemy_data,
            "enemy_level": enemy_level,
            "character_level": character_level,
            "talent_level": 10,
            "crystal_shrapnel_stacks": 6,
        }

        result = function(**context)
        action_results[global_frame_counter] = result

        # If this action created a buff, stamp its true global start_frame
        # (current global_frame_counter + the buff's own hitmark offset,
        # since a buff can trigger partway through an action's animation,
        # not just at the action's very start) BEFORE global_frame_counter
        # advances for the next action.
        buff_created = result.get("buff_created", None)
        if buff_created is not None:
            buff_created["start_frame"] = global_frame_counter + buff_created["hitmark"]
            buff_instances.append(buff_created)

        action_frames = character_data["talents"][talent_type]["action_frames"]
        global_frame_counter = global_frame_counter + action_frames

    return action_results

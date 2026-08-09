def is_buff_active(buff_instance, current_frame):
    # a buff is active from its start_frame (inclusive) up to
    # start_frame + duration (exclusive)
    buff_deactivation_frame = buff_instance["start_frame"] + buff_instance["duration"]
    return buff_instance["start_frame"] <= current_frame and current_frame < buff_deactivation_frame


def get_active_buff_totals(buff_instances, current_frame):
    # given a list of buff instances, returns a {stat: value} dict of only the
    # ones currently active at current_frame — ready to pass straight into
    # calculate_final_stats() as active_buffs
    active_buffs = {}
    for buff in buff_instances:
        if is_buff_active(buff_instance=buff, current_frame=current_frame):
            buff_value = buff["value"]
            buff_stat = buff["stat"]
            active_buffs[buff_stat] = buff_value
    return active_buffs

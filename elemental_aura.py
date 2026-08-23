AMPLIFYING_REACTIONS = {
    ("hydro", "pyro"): {"reaction": "vaporize", "multiplier": 2.0},   # Hydro triggers on existing Pyro
    ("pyro", "hydro"): {"reaction": "vaporize", "multiplier": 1.5},   # Pyro triggers on existing Hydro
    ("pyro", "cryo"): {"reaction": "melt", "multiplier": 2.0},        # Pyro triggers on existing Cryo
    ("cryo", "pyro"): {"reaction": "melt", "multiplier": 1.5},        # Cryo triggers on existing Pyro
}

OTHER_REACTIONS = {
    frozenset(["pyro", "electro"]): "overloaded",
    frozenset(["cryo", "electro"]): "superconduct",
    frozenset(["hydro", "electro"]): "electro_charged",
    frozenset(["hydro", "cryo"]): "frozen",
    frozenset(["pyro", "dendro"]): "burning",  # NOTE: sustained/ticking, not a one-time hit — needs different handling later
}
# NOT yet representable as simple pair lookups — each needs its own resolution logic:
# - Bloom: Dendro + Hydro creates a Core; Burgeon (Pyro) / Hyperbloom (Electro) are SEPARATE, later triggers that consume the Core
# - Shattered: Frozen (Cryo+Hydro) + a THIRD trigger (Geo or Claymore heavy hit)
SWIRL_REACTIONS = {
    ("anemo", "pyro"): {"reaction": "swirl", "element": "pyro", "deals_damage": True},
    ("anemo", "electro"): {"reaction": "swirl", "element": "electro", "deals_damage": True},
    ("anemo", "cryo"): {"reaction": "swirl", "element": "cryo", "deals_damage": True},
    ("anemo", "hydro"): {"reaction": "swirl", "element": "hydro", "deals_damage": False},
}

GEO_TRIGGERED_REACTIONS = {
    ("geo", "pyro"): "crystallize",
    ("geo", "cryo"): "crystallize",
    ("geo", "electro"): "crystallize",
    ("geo", "hydro"): "crystallize",  
}

LUNAR_REACTIONS_ORDER_INDEPENDENT = {
    frozenset(["dendro", "hydro"]): "lunar_bloom",
    frozenset(["hydro", "electro"]): "lunar_charged",
}
LUNAR_REACTIONS_ORDER_DEPENDENT = {
    ("geo", "hydro"): "lunar_crystallize",
}

REACTION_LEVEL_MULTIPLIERS = {
    "burning": {"20": 20.15, "40": 51.85, "50": 80.9, "60": 123.22, "70": 191.41, "80": 269.36, "90": 361.71, "95": 427.8, "100": 507.52},
    "swirl": {"20": 48.35, "40": 124.43, "50": 194.16, "60": 295.73, "70": 459.38, "80": 646.47, "90": 868.11, "95": 1026.72, "100": 1218.04},
    "superconduct": {"20": 120.88, "40": 311.07, "50": 485.4, "60": 739.33, "70": 1148.46, "80": 1616.17, "90": 2170.28, "95": 2566.8, "100": 3045.11},
    "electro_charged": {"20": 161.17, "40": 414.76, "50": 647.2, "60": 985.77, "70": 1531.28, "80": 2154.89, "90": 2893.71, "95": 3422.4, "100": 4060.14},
    "overloaded": {"20": 221.61, "40": 570.3, "50": 889.9, "60": 1355.43, "70": 2105.51, "80": 2962.97, "90": 3978.85, "95": 4705.79, "100": 5582.7},
    "shattered": {"20": 241.75, "40": 622.15, "50": 970.8, "60": 1478.65, "70": 2296.92, "80": 3232.33, "90": 4340.56, "95": 5133.59, "100": 6090.22},
    "bloom": {"20": 161.17, "40": 414.76, "50": 647.2, "60": 985.77, "70": 1531.28, "80": 2154.89, "90": 2893.71, "95": 3422.4, "100": 4060.14},
    "burgeon": {"20": 241.75, "40": 622.15, "50": 970.8, "60": 1478.65, "70": 2296.92, "80": 3232.33, "90": 4340.56, "95": 5133.59, "100": 6090.22},
    "hyperbloom": {"20": 241.75, "40": 622.15, "50": 970.8, "60": 1478.65, "70": 2296.92, "80": 3232.33, "90": 4340.56, "95": 5133.59, "100": 6090.22},
}

class ElementalAura:
    def __init__(self):
        self.applications = []

    def apply_element(self, gauge_units, element, current_frame):
        found_match = False
        for application in self.applications:
            if application["element"] == element:
                found_match = True
                taxed_value = gauge_units * 0.8
                new_value_wins = taxed_value > application["gauge_units"]
                if new_value_wins:
                    application["timestamp"] = current_frame
                    application["gauge_units"] = taxed_value
                    if element == "pyro":
                        application["decay"] = 2.5 * gauge_units + 7
        if found_match is False:
            self.applications.append({"element": element, "gauge_units": gauge_units * 0.8, "decay": 2.5 * gauge_units + 7, "timestamp": current_frame})
        return self.applications

    def get_current_gauge(self, current_frame, element):
        current_gauge = 0
        for application in self.applications:
            if application["element"] ==  element:
                t = (current_frame - application["timestamp"])/60
                base_duration = application["decay"]
                x = application["gauge_units"]
                current_gauge = (0.8 * x) * (1 - t/base_duration)
        return current_gauge
        
    def get_elemental_reactions(self, element):
        reaction = None
        for application in self.applications:
            trigger_element = element
            existing_element = application["element"]
            if element == "geo":
                reaction = GEO_TRIGGERED_REACTIONS.get(("geo", existing_element), None)
            elif element == "anemo":
                reaction = SWIRL_REACTIONS.get(("anemo", existing_element), None)
            else:
                reaction = AMPLIFYING_REACTIONS.get((trigger_element, existing_element), None)
                if reaction is None:
                    reaction = OTHER_REACTIONS.get(frozenset([trigger_element, existing_element]), None)
        return reaction



from typing import TYPE_CHECKING
from worlds.generic.Rules import set_rule
from .options import Goal

if TYPE_CHECKING:
    from . import AutoWorldWorld


def set_rules(world: "AutoWorldWorld") -> None:
    player = world.player
    multiworld = world.multiworld
    tiers = world.options.progression_tiers.value

    # Set entrance rules for tier unlocks
    for tier in range(2, tiers + 1):
        entrance_name = f"To Tier {tier}"
        entrance = multiworld.get_entrance(entrance_name, player)
        required_key = f"Tier {tier} Key"
        set_rule(entrance, lambda state, key=required_key, p=player: state.has(key, p))

    # Completion / Goal condition
    if world.options.goal.value == Goal.option_full_clear:
        # Require all keys up to max tier
        required_keys = [f"Tier {t} Key" for t in range(2, tiers + 1)]
        multiworld.completion_condition[player] = lambda state, keys=required_keys, p=player: all(
            state.has(k, p) for k in keys
        )
    else:
        # Default: Victory Token
        multiworld.completion_condition[player] = lambda state, p=player: state.has("Victory Token", p)

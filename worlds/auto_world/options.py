from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range


class LocationCount(Range):
    """
    Number of locations to generate for this slot.
    Locations are divided across the enabled progression tiers.
    """
    display_name = "Location Count"
    range_start = 5
    range_end = 300
    default = 20


class ProgressionTiers(Range):
    """
    Number of progression tiers.
    Locations in Tier N require the Tier N Key found in earlier tiers or other slots.
    """
    display_name = "Progression Tiers"
    range_start = 1
    range_end = 15
    default = 3


class CheckInterval(Range):
    """
    Default check interval in seconds for automated bots playing this slot.
    """
    display_name = "Default Check Interval"
    range_start = 1
    range_end = 3600
    default = 30


class CheckIntervalVariance(Range):
    """
    Percentage variance applied to check intervals (e.g. 30 means +/-30% random jitter on each check).
    """
    display_name = "Check Interval Variance (%)"
    range_start = 0
    range_end = 90
    default = 30


class Goal(Choice):
    """
    Goal condition required to complete the game:
    - Victory Token: Find the Victory Token placed in the multiworld.
    - Full Clear: Check all locations in this slot.
    """
    display_name = "Goal"
    option_victory_token = 0
    option_full_clear = 1
    default = 0


@dataclass
class AutoWorldOptions(PerGameCommonOptions):
    location_count: LocationCount
    progression_tiers: ProgressionTiers
    check_interval: CheckInterval
    check_interval_variance: CheckIntervalVariance
    goal: Goal

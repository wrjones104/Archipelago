from typing import Dict, List, Tuple
from BaseClasses import Location

BASE_LOCATION_ID = 8880000


class AutoWorldLocation(Location):
    game: str = "Auto World"


def generate_all_locations() -> Dict[str, int]:
    """Generates all possible location names and IDs for up to 15 tiers and 300 checks per tier."""
    table: Dict[str, int] = {}
    for tier in range(1, 16):
        for check in range(1, 301):
            name = f"Tier {tier} - Check {check}"
            code = BASE_LOCATION_ID + (tier * 1000) + check
            table[name] = code
    return table


LOCATION_TABLE: Dict[str, int] = generate_all_locations()
LOCATION_NAME_TO_ID: Dict[str, int] = LOCATION_TABLE.copy()


def get_locations_for_tiers(tiers: int, total_count: int) -> List[Tuple[str, int, str]]:
    """
    Distributes total_count checks across the requested number of tiers.
    Returns list of tuples: (location_name, location_id, region_name).
    """
    tiers = max(1, min(15, tiers))
    total_count = max(1, min(300, total_count))

    # Calculate count per tier
    base_per_tier = total_count // tiers
    remainder = total_count % tiers

    locations = []
    for tier in range(1, tiers + 1):
        tier_count = base_per_tier + (1 if tier <= remainder else 0)
        tier_count = min(300, tier_count)
        region_name = f"Tier {tier}"
        for check in range(1, tier_count + 1):
            name = f"Tier {tier} - Check {check}"
            code = LOCATION_NAME_TO_ID[name]
            locations.append((name, code, region_name))

    return locations

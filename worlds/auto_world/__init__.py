from typing import Dict, Any, List
from BaseClasses import Region, Entrance, ItemClassification, Tutorial
from worlds.AutoWorld import World, WebWorld
from .options import AutoWorldOptions, Goal
from .items import (
    AutoWorldItem, ITEM_TABLE, ITEM_NAME_TO_ID, FILLER_ITEMS
)
from .locations import (
    AutoWorldLocation, LOCATION_NAME_TO_ID, get_locations_for_tiers
)
from .rules import set_rules


class AutoWorldWeb(WebWorld):
    theme = "partyTime"
    tutorials = [Tutorial(
        "Auto World Setup Guide",
        "A guide to configuring and testing with Auto World.",
        "English",
        "setup_en.md",
        "setup/en",
        ["Archipelago"]
    )]


class AutoWorldWorld(World):
    """
    Auto World is a testing world designed for automated client bot execution,
    allowing automated multi-slot playback and Archipelago alerting verification.
    """
    game = "Auto World"
    options_dataclass = AutoWorldOptions
    options: AutoWorldOptions
    web = AutoWorldWeb()

    item_name_to_id = ITEM_NAME_TO_ID
    location_name_to_id = LOCATION_NAME_TO_ID

    def create_regions(self) -> None:
        menu_region = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu_region)

        tiers = self.options.progression_tiers.value
        loc_count = self.options.location_count.value
        location_data = get_locations_for_tiers(tiers, loc_count)

        tier_regions: Dict[str, Region] = {}
        for tier in range(1, tiers + 1):
            region_name = f"Tier {tier}"
            region = Region(region_name, self.player, self.multiworld)
            tier_regions[region_name] = region
            self.multiworld.regions.append(region)

            entrance = Entrance(self.player, f"To Tier {tier}", menu_region)
            menu_region.exits.append(entrance)
            entrance.connect(region)

        for loc_name, loc_id, region_name in location_data:
            loc = AutoWorldLocation(self.player, loc_name, loc_id, tier_regions[region_name])
            tier_regions[region_name].locations.append(loc)

    def create_items(self) -> None:
        tiers = self.options.progression_tiers.value
        item_pool: List[AutoWorldItem] = []

        # 1. Progression keys for tiers 2..N
        for tier in range(2, tiers + 1):
            item_pool.append(self.create_item(f"Tier {tier} Key"))

        # 2. Victory Token if goal is Victory Token
        if self.options.goal.value == Goal.option_victory_token:
            item_pool.append(self.create_item("Victory Token"))

        # 3. Fill the rest with filler / useful items
        total_locations = len(self.multiworld.get_unfilled_locations(self.player))
        needed_filler = total_locations - len(item_pool)
        for _ in range(needed_filler):
            item_pool.append(self.create_filler())

        self.multiworld.itempool += item_pool

    def set_rules(self) -> None:
        set_rules(self)

    def create_item(self, name: str) -> AutoWorldItem:
        item_data = ITEM_TABLE[name]
        return AutoWorldItem(name, item_data.classification, item_data.code, self.player)

    def get_filler_item_name(self) -> str:
        return self.random.choice(FILLER_ITEMS)

    def fill_slot_data(self) -> Dict[str, Any]:
        return {
            "location_count": self.options.location_count.value,
            "progression_tiers": self.options.progression_tiers.value,
            "check_interval": self.options.check_interval.value,
            "check_interval_variance": self.options.check_interval_variance.value,
            "goal": self.options.goal.value,
        }

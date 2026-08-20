from typing import Dict, Optional
from BaseClasses import Item, ItemClassification

BASE_ITEM_ID = 8880000


class AutoWorldItem(Item):
    game: str = "Auto World"


class ItemData:
    def __init__(self, code: int, classification: ItemClassification):
        self.code = code
        self.classification = classification


def generate_item_table() -> Dict[str, ItemData]:
    table: Dict[str, ItemData] = {}
    # Keys for tiers 2 through 15
    for tier in range(2, 16):
        table[f"Tier {tier} Key"] = ItemData(BASE_ITEM_ID + tier, ItemClassification.progression)

    # Progression Victory Item
    table["Victory Token"] = ItemData(BASE_ITEM_ID + 50, ItemClassification.progression)

    # Useful & Filler items
    table["Auto Booster"] = ItemData(BASE_ITEM_ID + 60, ItemClassification.useful)
    table["Test Energy"] = ItemData(BASE_ITEM_ID + 61, ItemClassification.useful)
    table["Data Packet"] = ItemData(BASE_ITEM_ID + 62, ItemClassification.useful)
    table["Filler Check"] = ItemData(BASE_ITEM_ID + 70, ItemClassification.filler)
    table["Test Ping"] = ItemData(BASE_ITEM_ID + 71, ItemClassification.filler)
    table["Speed Trap"] = ItemData(BASE_ITEM_ID + 80, ItemClassification.trap)

    return table


ITEM_TABLE: Dict[str, ItemData] = generate_item_table()
ITEM_NAME_TO_ID: Dict[str, int] = {name: data.code for name, data in ITEM_TABLE.items()}

FILLER_ITEMS = ["Filler Check", "Test Ping", "Data Packet", "Test Energy", "Auto Booster"]

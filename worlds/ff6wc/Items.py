from BaseClasses import Item
import typing
from typing import Dict


class ItemData(typing.NamedTuple):
    code: typing.Optional[int]
    progression: bool


item_table: Dict[str, ItemData] = {
    'TERRA': ItemData(501, True),
    'LOCKE': ItemData(502, True),
    'CYAN': ItemData(503, True),
    'SHADOW': ItemData(504, True),
    'EDGAR': ItemData(505, True),
    'SABIN': ItemData(506, True),
    'CELES': ItemData(507, True),
    'STRAGO': ItemData(508, True),
    'RELM': ItemData(509, True),
    'SETZER': ItemData(510, True),
    'MOG': ItemData(511, True),
    'GAU': ItemData(512, True),
    'GOGO': ItemData(513, True),
    'UMARO': ItemData(514, True),
    'Ramuh': ItemData(601, True),
    'Ifrit': ItemData(602, True),
    'Shiva': ItemData(603, True),
    'Siren': ItemData(604, True),
    'Terrato': ItemData(605, True),
    'Shoat': ItemData(606, True),
    'Maduin': ItemData(607, True),
    'Bismark': ItemData(608, True),
    'Stray': ItemData(609, True),
    'Palidor': ItemData(610, True),
    'Tritoch': ItemData(611, True),
    'Odin': ItemData(612, True),
    'Raiden': ItemData(613, True),
    'Bahamut': ItemData(614, True),
    'Alexandr': ItemData(615, True),
    'Crusader': ItemData(616, True),
    'Ragnarok Esper': ItemData(617, True),
    'Kirin': ItemData(618, True),
    'ZoneSeek': ItemData(619, True),
    'Carbunkl': ItemData(620, True),
    'Phantom': ItemData(621, True),
    'Sraphim': ItemData(622, True),
    'Golem': ItemData(623, True),
    'Unicorn': ItemData(624, True),
    'Fenrir': ItemData(625, True),
    'Starlet': ItemData(626, True),
    'Phoenix': ItemData(627, True),
    'Marvel Shoes': ItemData(701, False),
    'Cat Hood': ItemData(702, False),
    'Snow Muffler': ItemData(703, False),
    'Gem Box': ItemData(704, False),
    'ValiantKnife': ItemData(705, False),
    'Fixed Dice': ItemData(706, False),
    'Offering': ItemData(707, False),
    'Ragnarok Sword': ItemData(708, False),
    'Minerva': ItemData(709, False),
    'Exp. Egg': ItemData(710, False),
    'Illumina': ItemData(711, False),
    'Paladin Shld': ItemData(712, False),
    "Pearl Lance": ItemData(713, False),
    "Aura Lance": ItemData(714, False),
    "Magus Rod": ItemData(715, False),
    "Aegis Shld": ItemData(716, False),
    "Flame Shld": ItemData(717, False),
    "Ice Shld": ItemData(718, False),
    "Thunder Shld": ItemData(719, False),
    "Genji Shld": ItemData(720, False),
    "Force Shld": ItemData(721, False),
    "Red Cap": ItemData(722, False),
    "Genji Helmet": ItemData(723, False),
    "Force Armor": ItemData(724, False),
    "Genji Armor": ItemData(725, False),
    "BehemothSuit": ItemData(726, False),
    "Economizer": ItemData(727, False),
    "Genji Glove": ItemData(728, False),
    "Dragon Horn": ItemData(729, False)
}

filler_items = [
    'Marvel Shoes',
    'Cat Hood',
    'Snow Muffler',
    'Gem Box',
    'ValiantKnife',
    'Fixed Dice',
    'Offering',
    'Ragnarok Sword',
    'Minerva',
    'Exp. Egg',
    'Illumina',
    'Paladin Shld',
    "Pearl Lance",
    "Aura Lance",
    "Magus Rod",
    "Aegis Shld",
    "Flame Shld",
    "Ice Shld",
    "Thunder Shld",
    "Genji Shld",
    "Force Shld",
    "Red Cap",
    "Genji Helmet",
    "Force Armor",
    "Genji Armor",
    "BehemothSuit",
    "Economizer",
    "Genji Glove",
    "Dragon Horn"
]
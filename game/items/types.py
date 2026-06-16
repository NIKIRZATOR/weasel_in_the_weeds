from enum import Enum


class ItemKind(str, Enum):
    CONSUMABLE = "consumable"
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    QUEST = "quest"
    MATERIAL = "material"
    CURRENCY = "currency"


class EquipSlot(str, Enum):
    HELMET = "helmet"
    CHEST = "chest"
    BOOTS = "boots"
    WEAPON = "weapon"
    ACCESSORY = "accessory"
    ACCESSORY_1 = "accessory_1"
    ACCESSORY_2 = "accessory_2"

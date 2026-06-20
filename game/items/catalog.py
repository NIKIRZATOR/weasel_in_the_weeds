from game.items.models import ItemDefinition, ItemStack
from game.items.types import EquipSlot, ItemKind

ITEM_DEFINITIONS: dict[str, ItemDefinition] = {
    "coin": ItemDefinition(
        id="coin",
        name="Coin",
        kind=ItemKind.CURRENCY,
        stackable=True,
        max_stack=999999,
        price=1,
        description="A simple gold coin.",
    ),
    "test_item": ItemDefinition(
        id="test_item",
        name="test_item",
        kind=ItemKind.WEAPON,
        stackable=False,
        max_stack=1,
        equip_slot=EquipSlot.WEAPON,
        stats={"attack": 2},
        price=15,
        description="",
    ),
    "stick": ItemDefinition(
        id="stick",
        name="Stick",
        kind=ItemKind.MATERIAL,
        stackable=True,
        max_stack=999999,
        price=1,
        description="A simple stick.",
    ),
    "small_backpack": ItemDefinition(
        id="small_backpack",
        name="Small Backpack",
        kind=ItemKind.QUEST,
        stackable=False,
        max_stack=1,
        inventory_capacity_bonus=5,
        price=0,
        description="A small travel backpack from the hermit.",
    ),
    "map": ItemDefinition(
        id="map",
        name="Map",
        kind=ItemKind.QUEST,
        stackable=False,
        max_stack=1,
        price=0,
        description="A magical map that remembers opened places.",
    ),
}


def get_item_definition(item_id: str) -> ItemDefinition | None:
    return ITEM_DEFINITIONS.get(item_id)


def create_item_stack(item_id: str, quantity: int = 1) -> ItemStack | None:
    definition = get_item_definition(item_id)
    if definition is None:
        return None
    return ItemStack(definition, quantity)

from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent
from entity import Item

if TYPE_CHECKING:
    from entity import Actor, Item


class Inventory(BaseComponent):
    parent: Actor

    def __init__(self):
        self.items: List[Item] = []

    def drop(self, item: Item) -> None:
        """
        Removes an item from the inventory and restores it to the game map, at the player's current location.
        """
        self.items.remove(item)
        item.place(self.parent.x, self.parent.y, self.gamemap)

        self.engine.message_log.add_message(f"You dropped the {item.name}.")

    def add_token(self, token):
        consumed = False
        for other in self.items:
            if other.token == token:
                other.count += 1
                consumed = True
                break
        if not consumed:
            item = Item(
                char = ".",
                name = token.name,
                count = 1,
                token = token
            )
            item.parent = self
            self.items.append(item)

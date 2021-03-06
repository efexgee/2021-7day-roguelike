from __future__ import annotations
from random import choice
from math import ceil

from typing import TYPE_CHECKING

from entity import Item

import color
from components.base_component import BaseComponent
from render_order import RenderOrder

if TYPE_CHECKING:
    from entity import Actor


class Fighter(BaseComponent):
    parent: Actor

    def __init__(self, hp: int, base_defense: int, base_power: int, dmg_multipliers: dict[str,float]=None):
        self.max_hp = hp
        self._hp = hp
        self.base_defense = base_defense
        self.base_power = base_power
        if dmg_multipliers:
            self.dmg_multipliers = dmg_multipliers
        else:
            self.dmg_multipliers = {}

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()

    @property
    def defense(self) -> int:
        return self.base_defense + self.defense_bonus

    @property
    def power(self) -> int:
        return self.base_power + self.power_bonus

    @property
    def defense_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.defense_bonus
        else:
            return 0

    @property
    def power_bonus(self) -> int:
        if self.parent.equipment:
            return self.parent.equipment.power_bonus
        else:
            return 0

    def die(self) -> None:
        if self.engine.player is self.parent:
            death_message = "You died!"
            death_message_color = color.player_die
            self.parent.char = "%"
            self.parent.color = (191, 0, 0)
            self.parent.blocks_movement = False
            self.parent.ai = None
            self.parent.name = f"remains of {self.parent.name}"
            self.parent.render_order = RenderOrder.CORPSE
        else:
            death_message = f"{self.parent.name} is dead!"
            death_message_color = color.enemy_die
            self.parent.ai = None

        drop_targets = []
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                x = self.parent.x + dx
                y = self.parent.y + dy
                if x >= 0 and x < self.engine.game_map.width and y >= 0 and y < self.engine.game_map.height and self.engine.game_map.tiles["walkable"][x,y]:
                    drop_targets.append((x,y))
        for item in self.parent.inventory.items:
            (x,y) = choice(drop_targets)
            item.x = x
            item.y = y
            self.engine.game_map.queue_add_entity(item)
        for spell in self.parent.magic.spell_inventory.all_spells():
            (x,y) = choice(drop_targets)
            item = Item(
                x=x,
                y=y,
                char = "~",
                color = (255, 0, 255),
                name = "A spell",
                spell = spell,
            )
            self.engine.game_map.queue_add_entity(item)
        self.parent.inventory.items.clear()


        self.engine.message_log.add_message(death_message, death_message_color)

        self.engine.player.level.add_xp(self.parent.level.xp_given)

    def heal(self, amount: int) -> int:
        if self.hp == self.max_hp:
            return 0

        new_hp_value = self.hp + amount

        if new_hp_value > self.max_hp:
            new_hp_value = self.max_hp

        amount_recovered = new_hp_value - self.hp

        self.hp = new_hp_value

        return amount_recovered

    def take_damage(self, incoming_dmg: int, damage_type: str=None) -> None:
        modified_dmg = incoming_dmg
        if damage_type:
            dmg_multiplier = self.dmg_multipliers.get(damage_type)
            if dmg_multiplier:
                modified_dmg = ceil(incoming_dmg * dmg_multiplier)
                difference = modified_dmg - incoming_dmg
                if modified_dmg >= 0 and modified_dmg < incoming_dmg:
                    if self.engine.player is self.parent:
                        message_color = color.player_resists
                    else:
                        message_color = color.enemy_resists
                    self.parent.gamemap.engine.message_log.add_message(
                        f"{self.parent.name} only takes {modified_dmg} damage.",
                        message_color
                    )
                if difference > 0:
                    if self.engine.player is self.parent:
                        message_color = color.player_vulnerable
                    else:
                        message_color = color.enemy_vulnerable
                    self.parent.gamemap.engine.message_log.add_message(
                        f"{self.parent.name} takes {difference} additional damage!",
                        message_color
                    )
                # It's a heal instead.
                if modified_dmg < 0:
                    amount_healed = self.heal(-modified_dmg)
                    if amount_healed:
                        if self.engine.player is self.parent:
                            message_color = color.health_recovered
                        else:
                            message_color = color.enemy_health_recovered
                        self.parent.gamemap.engine.message_log.add_message(
                            f"{self.parent.name} heals for {amount_healed}!",
                            message_color
                        )
                    return

        self.hp -= modified_dmg

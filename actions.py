from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING
from tile_types import TileLabel
import entity_factories

import color
import exceptions
from components.magic import Spell
from spell_generator import SHARED_GRIMOIRE
from components.magic.token import *

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, Item


class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to."""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

        `self.engine` is the scope this action is being performed in.

        `self.entity` is the object performing the action.

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()


class ItemAction(Action):
    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        if self.item.consumable:
            self.item.consumable.activate(self)
        if self.item.magic:
            self.item.magic.activate(self)


class DropItem(ItemAction):
    def perform(self) -> None:
        if self.entity.equipment.item_is_equipped(self.item):
            self.entity.equipment.toggle_equip(self.item)

        self.entity.inventory.drop(self.item)


class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)

        self.item = item

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item)


class WaitAction(Action):
    def perform(self) -> None:
        pass

class CastRandomSpellAction(Action):
    def __init__(self, entity: Actor):
        self.caster = entity

    def perform(self) -> None:
        self.caster.magic.cast_random_spell()

class CastSpellAction(Action):
    def __init__(self, entity: Actor, spell: Spell, target: Optional[(int, int)]):
        self.caster = entity
        self.spell = spell
        self.target = target

    def perform(self) -> None:
        self.caster.magic.cast_spell(self.spell, self.target)


class TakeDownStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if self.engine.game_map.tiles[self.entity.x, self.entity.y]['label'] == TileLabel.Downstairs:
            self.engine.change_level(1)
            self.engine.message_log.add_message(
                "You descend the staircase.", color.descend
            )
        else:
            raise exceptions.Impossible("There are no down stairs here.")

class TakeUpStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if self.engine.game_map.tiles[self.entity.x, self.entity.y]['label'] == TileLabel.Upstairs:
            if self.engine.game_world.current_floor == 1:
                if self.engine.player.name == "The Avatar of Bamulet":
                    self.engine.player_failed = False
                else:
                    self.engine.player_failed = True

            else:
                self.engine.change_level(-1)
        else:
            raise exceptions.Impossible("There are no up stairs here.")


class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this actions destination.."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()


class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack.")

        self.entity.magic.cast_bump_spell(target)


class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is blocked by an entity.
            raise exceptions.Impossible("That way is blocked.")

        removed = set()
        self.entity.move(self.dx, self.dy)

        for item in self.engine.game_map.items:
            if self.entity.x == item.x and self.entity.y == item.y:
                if item.name == "The Blender of Bamulet":
                    if self.entity is self.engine.familiar:
                        return
                    (x, y) = (self.entity.x, self.entity.y)
                    self.engine.game_map.entities.remove(self.entity)
                    if self.entity is self.engine.player:
                        avatar = entity_factories.avatar_of_bamulet
                        avatar.magic.spell_inventory.bump_spell_free = SHARED_GRIMOIRE["avatar_spell"]
                        self.engine.player = avatar.spawn(self.engine.game_map, x, y)
                        self.engine.reveal_squirrels_true_nature()
                        self.engine.message_log.add_message(f"The Avatar of Bamulet Arises! Return to the surface!")
                    else:
                       avatar = entity_factories.corrupt_avatar_of_bamulet
                       avatar.magic.spell_inventory.bump_spell_free = SHARED_GRIMOIRE["avatar_spell"]
                       avatar.spawn(self.engine.game_map, x, y)
                       self.engine.message_log.add_message(f"The Corrupted Avatar of Bamulet arises, all mortals beware!!")
                    self.engine.game_map.entities.remove(item)
                    return

                if item.token:
                    for _ in range(0, item.count):
                        self.entity.inventory.add_token(item.token)
                elif item.spell:
                    self.entity.magic.spell_inventory.other_spell.append(item.spell)
                removed.add(item)

                if self.entity is self.engine.player:
                    self.engine.message_log.add_message(f"You picked up the {item.name}!")


        self.engine.game_map.entities = self.engine.game_map.entities.difference(removed)


class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor and self.target_actor.blocks_movement:
            return MeleeAction(self.entity, self.dx, self.dy).perform()

        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()

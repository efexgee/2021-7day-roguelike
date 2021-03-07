from __future__ import annotations

import copy

import random
from typing import List, Optional, Tuple, TYPE_CHECKING
from entity import Actor

import numpy as np  # type: ignore
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction, CastSpellAction
from input_handlers import cast_action
from spell_generator import random_spell

if TYPE_CHECKING:
    from entity import Actor


class BaseAI(Action):
    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """Compute and return a path to the target position.

        If there is no valid path then returns an empty list.
        """
        # Copy the walkable array.
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int16)
        cost += self.entity.gamemap.tiles["damage"] * 10

        for entity in self.entity.gamemap.entities:
            # Check that an entity blocks movement and the cost isn't zero (blocking.)
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will crowd behind each other in
                # hallways.  A higher number means enemies will take longer paths in
                # order to surround the player.
                cost[entity.x, entity.y] += 10

        # Create a graph from the cost array and pass that graph to a new pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # Start position.

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]


class Familiar(BaseAI):
    def __init__(self, entity: Actor):
        self.entity = entity

    def perform(self) -> None:
        for item in self.entity.inventory.items:
            for _ in range(item.count):
                self.engine.player.inventory.add_token(item.token)
        for spell in self.entity.magic.spell_inventory.other_spell:
            self.engine.player.magic.spell_inventory.other_spell.append(spell)
        self.entity.magic.spell_inventory.other_spell.clear()
        self.entity.inventory.items.clear()

        player_weight = 1
        token_weight = 1
        wiggle_weight = 1
        player_dist = self.entity.distance(self.engine.player.x, self.engine.player.y)
        if player_dist < 4:
            player_weight = 1
            token_weight = 10
            wiggle_weight = 10
        elif player_dist < 10:
            player_weight = 1
            token_weight = 1
            wiggle_weight = 0
        else:
            player_weight = 100
            token_weight = 0
            wiggle_weight = 0

        dist = self.engine.pathing.token_flow * token_weight + self.engine.pathing.player_flow * player_weight + (self.engine.pathing.random_flow + 100) * wiggle_weight
        path = self.engine.pathing.path_along_flow(dist, self.entity.x, self.entity.y)
        if path:
            dest_x, dest_y = path.pop(0)
            return MovementAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()

class DummyAI(BaseAI):
    def __init__(self, entity: Actor):
        pass

    def perform(self) -> None:
        pass

class SpawnerAI(BaseAI):
    def __init__(self, entity: Actor, prob, spawn_fn):
        self.entity = entity
        self.spawn_fn = spawn_fn
        self.prob = prob

    def perform(self) -> None:
        if random.random() < self.prob:
            drop_targets = []
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    x = self.entity.x + dx
                    y = self.entity.y + dy
                    if x >= 0 and x < self.engine.game_map.width and y >= 0 and y < self.engine.game_map.height and self.engine.game_map.tiles["walkable"][x,y]:
                        if not self.engine.game_map.get_blocking_entity_at_location(x,y):
                            drop_targets.append((x,y))
            if drop_targets:
                (x,y) = random.choice(drop_targets)
                new_entity = self.spawn_fn()
                new_entity.x = x
                new_entity.y = y
                new_entity.spawn(self.engine.game_map, x, y)

class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        path = None
        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            flow = self.engine.pathing.player_flow 
            path = self.engine.pathing.path_along_flow(flow, self.entity.x, self.entity.y)

        if path:
            dest_x, dest_y = path.pop(0)
            return BumpAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()

class RangedHostileEnemy(BaseAI):
    def __init__(self, entity: Actor, spell_fn = None):
        super().__init__(entity)
        self.spell_fn = spell_fn

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        path = None
        spell = self.entity.magic.spell_inventory.ranged_spell
        if self.spell_fn:
            spell = self.spell_fn(self.entity)
        if spell and spell.can_cast(self.entity.inventory):
            range = spell.attributes().get("range", 0)
            if distance <= 2:
                path = self.engine.pathing.path_along_flow(self.engine.pathing.anti_player_flow, self.entity.x, self.entity.y)
            elif distance <= range:
                return CastSpellAction(self.entity, spell, (target.x, target.y)).perform()
            else:
                if self.engine.game_map.visible[self.entity.x, self.entity.y]:
                    path = self.engine.pathing.path_along_flow(self.engine.pathing.player_flow, self.entity.x, self.entity.y)
                else:
                    path = self.engine.pathing.path_along_flow(self.engine.pathing.random_flow, self.entity.x, self.entity.y)
        else:
            flow = self.engine.pathing.mushroom_flow + self.engine.pathing.token_flow
            flow[self.entity.x, self.entity.y] = 1000
            path = self.engine.pathing.path_along_flow(flow, self.entity.x, self.entity.y)

        if path:
            dest_x, dest_y = path.pop(0)
            return BumpAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()

        return WaitAction(self.entity).perform()


class ConfusedEnemy(BaseAI):
    """
    A confused enemy will stumble around aimlessly for a given number of turns, then revert back to its previous AI.
    If an actor occupies a tile it is randomly moving into, it will attack.
    """

    def __init__(
        self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int
    ):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    def perform(self) -> None:
        # Revert the AI back to the original state if the effect has run its course.
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"The {self.entity.name} is no longer confused."
            )
            self.entity.ai = self.previous_ai
        else:
            # Pick a random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # Northwest
                    (0, -1),  # North
                    (1, -1),  # Northeast
                    (-1, 0),  # West
                    (1, 0),  # East
                    (-1, 1),  # Southwest
                    (0, 1),  # South
                    (1, 1),  # Southeast
                ]
            )

            self.turns_remaining -= 1

            # The actor will either try to move or attack in the chosen random direction.
            # It's possible the actor will just bump into the wall, wasting a turn.
            return BumpAction(self.entity, direction_x, direction_y,).perform()

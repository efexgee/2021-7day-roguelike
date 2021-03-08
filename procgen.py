from __future__ import annotations
from collections import defaultdict
import numpy as np

from collections import Counter

import random
from typing import Dict, Iterator, List, Tuple, TYPE_CHECKING

import tcod

from entity import Item
import entity_factories
from game_map import GameMap
from tile_types import floor, down_stairs, TileLabel
from components.magic.token import all_tokens


if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.orc, 80),
        (entity_factories.giant_rat, 100),
        (entity_factories.imp, 30),
        (entity_factories.goblin_wizard, 70),
        (entity_factories.squirrel, 100),
        (entity_factories.mushroom, 100)],
    2: [(entity_factories.giant_rat, 50)],
    3: [(entity_factories.troll, 15),
        (entity_factories.squirrel, 0),
        (entity_factories.woody_mushroom, 100),
        (entity_factories.fire_elem, 5),
        (entity_factories.giant_rat, 0)],
    5: [(entity_factories.troll, 30),
        (entity_factories.fire_elem, 30)],
    7: [(entity_factories.troll, 60),
        (entity_factories.fire_elem, 50)],
}


def get_max_value_for_floor(
    max_value_by_floor: List[Tuple[int, int]], floor: int
) -> int:
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value


def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
    number_of_entities: int,
    floor: int,
) -> List[Entity]:
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    if entities:
        chosen_entities = random.choices(
            entities, weights=entity_weighted_chance_values, k=number_of_entities
        )

        return [e for factory in chosen_entities for e in factory()]
    else:
        return []


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def contains(self, x, y):
        return (
            self.x1 <= x
            and self.x2 >= x
            and self.y1 <= y
            and self.y2 >= y
        )


    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def place_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int,) -> None:
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )

    tokens = all_tokens()

    for monster in monsters:
        monster.magic.assure_castability(monster.magic.spell_inventory.ranged_spell, 10)
        monster.magic.assure_castability(monster.magic.spell_inventory.bump_spell, 10)
        monster.magic.assure_castability(monster.magic.spell_inventory.heal_spell, 10)
        for _ in range(30):
            token = random.choice(tokens)
            monster.inventory.add_token(token())

    for entity in monsters:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)


def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    engine: Engine,
) -> GameMap:
    """Generate a new dungeon map."""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []

    center_of_last_room = (0, 0)

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = floor

        if len(rooms) == 0:
            # The first room, where the player starts.
            player.place(*new_room.center, dungeon)

        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            touched_rooms = {len(rooms)}
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                if (TileLabel(dungeon.tiles[x,y]["label"]).name == "Wall"):
                    dungeon.tiles[x, y] = floor

            center_of_last_room = new_room.center

        place_entities(new_room, dungeon, engine.game_world.current_floor)

        dungeon.downstairs_location = center_of_last_room

        # Finally, append the new room to the list.
        rooms.append(new_room)

    if engine.game_world.current_floor == 3:
        block_access((player.x, player.y), center_of_last_room, dungeon)

    dungeon.tiles[dungeon.downstairs_location] = down_stairs
    engine.familiar.spawn(dungeon, player.x+1, player.y)

    return dungeon


def block_access(start, end, dungeon):
    while True:
        cost = np.array(dungeon.tiles["walkable"], dtype=np.int16)
        for entity in dungeon.actors:
            cost[entity.x, entity.y] = 0
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)
        pathfinder.add_root(start)
        path = pathfinder.path_to(end)[1:].tolist()

        if not path:
            return

        i = path[len(path)//2]
        entity = entity_factories.individual_mushroom(1.0)
        entity.spawn(dungeon, i[0], i[1])

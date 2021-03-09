from __future__ import annotations
from collections import defaultdict

import lzma
import pickle
from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

import exceptions
from message_log import MessageLog
import render_functions
from tile_types import TileLabel

from pathing import PathingCache
from spell_visualization import SpellVisualizationOverlay

from entity import Actor
from game_map import GameMap, GameWorld


class Engine:
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor, familiar: Actor):
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player
        self.familiar = familiar
        self.pathing = PathingCache(self)
        self.spell_overlay = SpellVisualizationOverlay(self)
        self.player_failed = None
        self.persisted_levels = {}

    def change_level(self, delta):
        if self.game_world.current_floor > 0:
            self.persisted_levels[self.game_world.current_floor] = (self.player.x, self.player.y, self.game_map)
        new_level = self.game_world.current_floor + delta
        self.game_world.current_floor = new_level
        if new_level not in self.persisted_levels:
            self.game_world.generate_floor()
            self.update_fov()
        else:
            (x, y, self.game_map) = self.persisted_levels[new_level]
            self.player.x = x
            self.player.y = y
            self.player.parent = self.game_map
            self.game_map.entities.add(self.player)
            self.update_fov()

    def check_environment_interactions(self) -> None:
        for actor in set(self.game_map.actors):
            damage = self.game_map.tiles["damage"][actor.x, actor.y]
            if damage:
                env_hazard = TileLabel(self.game_map.tiles['label'][actor.x, actor.y]).name
                if actor is self.player:
                    message_color = color.player_dmg
                else:
                    message_color = color.enemy_dmg
                outcome_text = actor.fighter.damage(damage, env_hazard)
                self.message_log.add_message(
                    f"{actor.name} is standing in {env_hazard} which {outcome_text}.",
                    message_color
                )

    def reveal_squirrels_true_nature(self):
        from components.ai import RangedHostileEnemy
        from components.equipment import Equipment
        from components.fighter import Fighter
        from components.inventory import Inventory
        from components.level import Level
        from components.magic import Magic
        from entity import Actor, Item
        import entity_factories
        import copy
        sq = Actor(
        char=".",
        color=(127, 127, 0),
        name="Secret Squirrel Cultist of Blamulet, Bamulet's Feckless Cousin (not harmless)",
        ai_cls=RangedHostileEnemy,
        equipment=Equipment(),
        fighter=Fighter(hp=10, base_defense=2, base_power=3, dmg_multipliers={"fire": -0.2}),
        magic=Magic(),
        inventory=Inventory(),
        level=Level(xp_given=175),
        )
        sq.magic.fill_advanced_spell_slots()
        sq.magic.assure_castability(sq.magic.spell_inventory.ranged_spell, 10)
        sq.magic.assure_castability(sq.magic.spell_inventory.bump_spell, 10)
        sq.magic.assure_castability(sq.magic.spell_inventory.heal_spell, 10)
        def squirrel_cultist():
            return[sq]
        entity_factories.squirrel = squirrel_cultist
        to_remove = set()
        to_add = set()
        for (i, entity) in enumerate(self.game_map.entities):
            if entity.name == "Squirrel (super harmless)":
                sq = copy.deepcopy(sq)
                sq.x = entity.x
                sq.y = entity.y
                sq.parent = self.game_map
                to_remove.add(entity)
                to_add.add(sq)
        self.game_map.entities = self.game_map.entities.difference(to_remove).union(to_add)
        for (x, y, gm) in self.persisted_levels.values():
            to_remove = set()
            to_add = set()
            for (i, entity) in enumerate(gm.entities):
                if entity.name == "Squirrel (super harmless)":
                    sq = copy.deepcopy(sq)
                    sq.x = entity.x
                    sq.y = entity.y
                    sq.parent = gm
                    gm.entities[i] = sq
            gm.entitie = gm.entities.difference(to_remove).union(to_add)


    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass  # Ignore impossible action exceptions from AI.

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console) -> None:
        self.game_map.render(console)

        self.message_log.render(console=console, x=21, y=45, width=40, height=5)
        self.player.magic.spell_inventory.render(console=console, x=65, y=45, width=40, height=5)

        render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
        )

        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, 47),
        )

        render_functions.render_names_at_mouse_location(
            console=console, x=21, y=44, engine=self
        )

    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)

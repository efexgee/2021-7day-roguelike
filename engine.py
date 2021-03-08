from __future__ import annotations

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

if TYPE_CHECKING:
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

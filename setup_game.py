"""Handle the loading and initialization of game sessions."""
from __future__ import annotations

from collections import Counter

from the_will_of_bamulet import SmitedByBamulet

import copy
import lzma
import pickle
import traceback
from typing import Optional

import tcod

import color
from engine import Engine
import entity_factories
from game_map import GameWorld
import input_handlers
from components.magic.token import *
from entity import Item

from components.magic import Spell
from components.magic.token import *
from spell_generator import fill_shared_grimoire

from spell_generator import fill_shared_grimoire, random_small_construction

# Load the background image and remove the alpha channel.
background_image = tcod.image.load("menu_background.png")[:, :, :3]


def new_game() -> Engine:
    """Return a brand new game session as an Engine instance."""
    map_width = 80
    map_height = 43

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    fill_shared_grimoire()

    player = copy.deepcopy(entity_factories.player)
    player.magic.fill_default_spell_slots()
    player.magic.spell_inventory.other_spell.append(random_small_construction())
    player.magic.assure_castability(player.magic.spell_inventory.other_spell[0], 10)
    player.magic.assure_castability(player.magic.spell_inventory.ranged_spell, 10)
    player.magic.assure_castability(player.magic.spell_inventory.bump_spell, 10)
    player.magic.assure_castability(player.magic.spell_inventory.heal_spell, 10)
    player.magic.assure_castability(player.magic.spell_inventory.summon_spell, 10)

    familiar = copy.deepcopy(entity_factories.familiar)

    engine = Engine(player=player, familiar=familiar)


    engine.game_world = GameWorld(
        engine=engine,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
    )

    engine.change_level(1)

    engine.message_log.add_message(
        "Hello and welcome, adventurer, to yet another dungeon!", color.welcome_text
    )

    return engine


def load_game(filename: str) -> Engine:
    """Load an Engine instance from a file."""
    with open(filename, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    return engine


class MainMenu(input_handlers.BaseEventHandler):
    """Handle the main menu rendering and input."""

    def on_render(self, console: tcod.Console) -> None:
        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "Quest for the Blender of Bamulet",
            fg=color.menu_title,
            alignment=tcod.CENTER,
        )
        console.print(
            console.width // 2,
            console.height // 2 - 3,
            "or an exercise in squirrels",
            fg=color.menu_text,
            alignment=tcod.CENTER,
        )

        menu_width = 24
        console.print(
            console.width // 2,
            console.height // 2 - 1,
            "Any key to begin...".ljust(menu_width),
            fg=color.menu_text,
            bg=color.black,
            alignment=tcod.CENTER,
            bg_blend=tcod.BKGND_ALPHA(64),
        )

    def ev_keydown(
        self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        return input_handlers.MainGameEventHandler(new_game())

class EndGameFail(input_handlers.BaseEventHandler):
    def on_render(self, console: tcod.Console) -> None:
        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "You return to the surface without The Blender. Bamulet punishes you thusly...",
            fg=color.menu_title,
            alignment=tcod.CENTER,
        )

    def ev_keydown(
        self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        raise SmitedByBamulet

class EndGameSuccess(input_handlers.BaseEventHandler):
    def on_render(self, console: tcod.Console) -> None:
        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "You return to the surface with The Blender. Bamulet is pleased. A great feast of squirrels is held.",
            fg=color.menu_title,
            alignment=tcod.CENTER,
        )
    def ev_keydown(
        self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        raise SystemExit(0)

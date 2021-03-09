#!/usr/bin/env python3
import traceback
import time

import tcod

import color
import exceptions
import setup_game
import input_handlers


def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    """If the current event handler has an active Engine then save it."""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print("Game saved.")


def main() -> None:
    screen_width = 100
    screen_height = 90

    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()

    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title="Yet Another Roguelike Tutorial",
        vsync=True,
    ) as context:
        root_console = tcod.Console(screen_width, screen_height, order="F")
        while True:
            root_console.clear()
            if isinstance(handler, input_handlers.EventHandler):
                if handler.engine.spell_overlay.active_effects:
                    handler.on_render(console=root_console)
                    if handler.engine.spell_overlay.on_render(console=root_console):
                        context.present(root_console)
                        time.sleep(0.25)
            handler.on_render(console=root_console)
            context.present(root_console)

            for event in tcod.event.wait():
                context.convert_event(event)
                handler = handler.handle_events(event)
            if isinstance(handler, input_handlers.EventHandler):
                if handler.engine.player_failed is not None:
                    if handler.engine.player_failed:
                        handler = setup_game.EndGameFail()
                    else:
                        handler = setup_game.EndGameSuccess()
if __name__ == "__main__":
    main()

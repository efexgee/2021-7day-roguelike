from typing import Tuple

import numpy as np  # type: ignore
from enum import IntEnum, auto

# Tile labels
class TileLabel(IntEnum):
    Floor = auto()
    Wall = auto()
    Downstairs = auto()
    Fire = auto()
    Acid = auto()

# Tile graphics structured type compatible with Console.tiles_rgb.
graphic_dt = np.dtype(
    [
        ("ch", np.int32),  # Unicode codepoint.
        ("fg", "3B"),  # 3 unsigned bytes, for RGB colors.
        ("bg", "3B"),
    ]
)

# Tile struct used for statically defined tile data.
tile_dt = np.dtype(
    [
        ("label", int), # Used in messages
        ("walkable", np.bool),  # True if this tile can be walked over.
        ("transparent", np.bool),  # True if this tile doesn't block FOV.
        ("dark", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light", graphic_dt),  # Graphics for when the tile is in FOV.
        ("damage", int), # Non-zero if this tile deals damage.
    ]
)


def new_tile(
    *,  # Enforce the use of keywords, so that parameter order doesn't matter.
    label: int,
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    damage: int,
) -> np.ndarray:
    """Helper function for defining individual tile types """
    return np.array((label, walkable, transparent, dark, light, damage), dtype=tile_dt)


# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

floor = new_tile(
    label=TileLabel.Floor,
    walkable=True,
    transparent=True,
    dark=(ord(" "), (255, 255, 255), (50, 50, 150)),
    light=(ord(" "), (255, 255, 255), (200, 180, 50)),
    damage=0,
)
wall = new_tile(
    label=TileLabel.Wall,
    walkable=False,
    transparent=False,
    dark=(ord(" "), (255, 255, 255), (0, 0, 100)),
    light=(ord(" "), (255, 255, 255), (130, 110, 50)),
    damage=0,
)
down_stairs = new_tile(
    label=TileLabel.Downstairs,
    walkable=True,
    transparent=True,
    dark=(ord(">"), (0, 0, 100), (50, 50, 150)),
    light=(ord(">"), (255, 255, 255), (200, 180, 50)),
    damage=0,
)
fire = new_tile(
    label=TileLabel.Fire,
    walkable=True,
    transparent=True,
    dark=(ord("^"), (220, 200, 130), (50, 50, 150)),
    light=(ord("^"), (255, 100, 0), (200, 180, 50)),
    damage=3,
)
acid = new_tile(
    label=TileLabel.Acid,
    walkable=True,
    transparent=True,
    dark=(ord("^"), (0, 200, 230), (50, 50, 150)),
    light=(ord("^"), (0, 255, 100), (200, 180, 50)),
    damage=5,
)

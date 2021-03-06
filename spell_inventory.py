import tcod
import color

class SpellInventory:
    def __init__(self, parent):
        self.ranged_spell = None
        self.bump_spell = None
        self.heal_spell = None
        self.parent = parent

    def render(
        self, console: tcod.Console, x: int, y: int, width: int, height: int,
    ):
        y_offset = height - 1
        if self.ranged_spell:
            count = self.ranged_spell.max_casts(self.parent.parent.inventory)
            console.print(x=x, y=y + y_offset, string=f"ranged: {count}", fg=color.white)
            y_offset -= 1
        if self.bump_spell:
            count = self.bump_spell.max_casts(self.parent.parent.inventory)
            console.print(x=x, y=y + y_offset, string=f"melee: {count}", fg=color.white)
            y_offset -= 1
        if self.heal_spell:
            count = self.heal_spell.max_casts(self.parent.parent.inventory)
            console.print(x=x, y=y + y_offset, string=f"heal: {count}", fg=color.white)

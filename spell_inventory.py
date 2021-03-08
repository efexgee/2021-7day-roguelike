import tcod
import color

class SpellInventory:
    def __init__(self, parent):
        self.ranged_spell = None
        self.bump_spell = None
        self.bump_spell_free = None
        self.heal_spell = None
        self.summon_spell = None
        self.other_spell = []
        self.parent = parent

    def render(
        self, console: tcod.Console, x: int, y: int, width: int, height: int,
    ):
        y_offset = height - 1
        if self.ranged_spell:
            count = self.ranged_spell.max_casts(self.parent.parent.inventory)
            console.print(x=x, y=y + y_offset, string=f"{self.ranged_spell.name()}: {count}", fg=color.white)
            y_offset -= 1
        if self.bump_spell:
            count = self.bump_spell.max_casts(self.parent.parent.inventory)
            console.print(x=x, y=y + y_offset, string=f"{self.bump_spell.name()}: {count}", fg=color.white)
            y_offset -= 1
        if self.heal_spell:
            count = self.heal_spell.max_casts(self.parent.parent.inventory)
            console.print(x=x, y=y + y_offset, string=f"{self.heal_spell.name()}: {count}", fg=color.white)
            y_offset -= 1
        if self.summon_spell:
            count = self.summon_spell.max_casts(self.parent.parent.inventory)
            console.print(x=x, y=y + y_offset, string=f"{self.summon_spell.name()}: {count}", fg=color.white)
            y_offset -= 1
        if self.other_spell:
            count = self.other_spell[0].max_casts(self.parent.parent.inventory)
            console.print(x=x, y=y + y_offset, string=f"{self.other_spell[0].name()}: {count}", fg=color.white)
            y_offset -= 1

    def all_spells(self):
        return [s for s in [
            self.ranged_spell,
            self.bump_spell,
            self.heal_spell,
            self.summon_spell,
        ] + self.other_spell if s]

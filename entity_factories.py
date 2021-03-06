from components.ai import HostileEnemy, RangedHostileEnemy, DummyAI
from components import consumable, equippable
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from components.magic import Magic
from components.magic.token import *
from entity import Actor, Item
from spell_generator import random_spell_with_constraints


player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=1, base_power=2),
    magicable=Magic(),
    inventory=Inventory(),
    level=Level(level_up_base=200),
)

def orc():
  o = Actor(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=3),
    inventory=Inventory(),
    magicable=Magic(),
    level=Level(xp_given=35),
    )
  o.magicable.fill_default_spell_slots()
  return [o]


def mushroom():
    return [Actor(
    char="m",
    color=(63, 127, 63),
    name="Mushroom",
    ai_cls=DummyAI,
    equipment=Equipment(),
    fighter=Fighter(hp=5, base_defense=0, base_power=3),
    inventory=Inventory(),
    magicable=Magic(),
    level=Level(xp_given=35),
    ) for _ in range(0, 5)]

def imp_spell(imp):
    def is_valid(spell):
        base_damage = spell.attributes().get("base_damage", 0)
        if base_damage > 20:
            return False
        return True
    return random_spell_with_constraints(is_valid, [i.token for i in imp.inventory.items])

def imp():
    return [Actor(
    char="i",
    color=(63, 127, 63),
    name="Imp",
    ai_cls=lambda parent: RangedHostileEnemy(parent, imp_spell),
    equipment=Equipment(),
    fighter=Fighter(hp=5, base_defense=0, base_power=3),
    inventory=Inventory(),
    magicable=Magic(),
    level=Level(xp_given=35),
    )]

def goblin_wizard():
    g = Actor(
    char="g",
    color=(63, 127, 63),
    name="Goblin Wizard (very wise)",
    ai_cls=lambda parent: RangedHostileEnemy(parent),
    equipment=Equipment(),
    fighter=Fighter(hp=5, base_defense=0, base_power=3),
    inventory=Inventory(),
    magicable=Magic(),
    level=Level(xp_given=35),
    )
    g.magicable.fill_default_spell_slots()
    return [g]

def troll():
    t = Actor(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=1, base_power=4),
    magicable=Magic(),
    inventory=Inventory(),
    level=Level(xp_given=100),
    )
    t.magicable.fill_default_spell_slots()
    return [t]

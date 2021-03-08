from components.ai import HostileEnemy, RangedHostileEnemy, DummyAI, Familiar, SpawnerAI
from components import consumable, equippable
from components.equipment import Equipment
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from components.magic import Magic
from components.magic.token import *
from entity import Actor, Item
from spell_generator import random_spell_with_constraints
from random import gammavariate

player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=3000, base_defense=1, base_power=2,
        dmg_multipliers={
            "fire": 1.5,
            "poop": 0.8,
            "strong coffee": -1.0}
    ),
    magic=Magic(),
    inventory=Inventory(),
    level=Level(level_up_base=200),
)
familiar = Actor(
    char="f",
    color=(0, 0, 0),
    name="Canny Black Cat",
    ai_cls=Familiar,
    equipment=Equipment(),
    fighter=Fighter(hp=30, base_defense=1, base_power=2),
    magic=Magic(),
    inventory=Inventory(),
    level=Level(xp_given=0),
)
familiar.blocks_movement = False

def orc():
  o = Actor(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=0, base_power=3),
    inventory=Inventory(),
    magic=Magic(),
    level=Level(xp_given=35),
    )
  o.magic.fill_default_spell_slots()
  return [o]


def individual_mushroom():
    return Actor(
    char="m",
    color=(63, 127, 63),
    name="Mushroom",
    ai_cls=lambda parent: SpawnerAI(parent, 0.01, individual_mushroom),
    equipment=Equipment(),
    fighter=Fighter(hp=1, base_defense=0, base_power=3),
    inventory=Inventory(),
    magic=Magic(),
    level=Level(xp_given=10),
    )

def mushroom():
    return [individual_mushroom() for _ in range(0, 7)]

def imp_spell(imp):
    def is_valid(spell):
        base_damage = spell.attributes.get("base_damage", 0)
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
    magic=Magic(),
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
    magic=Magic(),
    level=Level(xp_given=35),
    )
    g.magic.fill_default_spell_slots()
    return [g]

def troll():
    t = Actor(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=16, base_defense=1, base_power=4),
    magic=Magic(),
    inventory=Inventory(),
    level=Level(xp_given=100),
    )
    t.magic.fill_default_spell_slots()
    return [t]

def fire_elem():
    fe = Actor(
    char="E",
    color=(127, 0, 0),
    name="Fire Elemental",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=10, base_defense=2, base_power=3, dmg_multipliers={"fire": -0.2}),
    magic=Magic(),
    inventory=Inventory(),
    level=Level(xp_given=175),
    )
    fe.magic.fill_default_spell_slots()
    return[fe]

def giant_rat():
    gr = Actor(
    char="r",
    color=(127, 127, 0),
    name="Giant Rat",
    ai_cls=HostileEnemy,
    equipment=Equipment(),
    fighter=Fighter(hp=3, base_defense=0, base_power=1, dmg_multipliers={"poop": 0.5, "strong coffee": 3.0 }),
    magic=Magic(),
    inventory=Inventory(),
    level=Level(xp_given=5),
    )
    num_rats = int(gammavariate(2,2)) + 3
    rat_list = []
    for rat in range(0, num_rats):
        gr.magic.fill_default_spell_slots()
        rat_list.append(gr)
    return rat_list

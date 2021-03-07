from random import Random, randint, shuffle
from components.magic.token import *
from components.magic import Spell

SHARED_GRIMOIRE = {}


def random_small_ranged():
    def is_valid(spell):
        if len(spell.tokens) > 6:
            return False
        attributes = spell.attributes()
        if not attributes.get("requires_target", False):
            return False
        if attributes.get("range", 0) < 4 or attributes.get("range", 0) <= attributes.get("AOE_radius", 0):
            return False
        base_damage = attributes.get("base_damage", 0)
        if base_damage > 3 or base_damage < 1:
            return False
        return True
    return random_spell_with_constraints(is_valid)

def random_small_bump():
    def is_valid(spell):
        if len(spell.tokens) > 6:
            return False
        attributes = spell.attributes()
        if not attributes.get("requires_target", False):
            return False
        if attributes.get("range", 0) != 1.5 or attributes.get("AOE_radius", 0) != 0:
            return False
        base_damage = attributes.get("base_damage", 0)
        if base_damage > 3 or base_damage < 1:
            return False
        return True
    return random_spell_with_constraints(is_valid)

def random_small_heal():
    def is_valid(spell):
        if len(spell.tokens) > 6:
            return False
        attributes = spell.attributes()
        if not attributes.get("targets_caster", False):
            return False
        if attributes.get("AOE_radius", 0) > 0:
            return False
        base_damage = attributes.get("base_damage", 0)
        if base_damage < -10 or base_damage > -1:
            return False
        return True
    return random_spell_with_constraints(is_valid)

def random_spell_with_constraints(is_valid_fn, tokens=None):
    if tokens is None:
        tokens = [t() for t in all_tokens()]

    spell = None
    remaining_tries = 5000
    cache = set()
    while not spell or not is_valid_fn(spell):
        if remaining_tries <= 0:
            return None
        spell = random_spell(tokens, cache)
        remaining_tries -= 1
    return spell


def random_spell(all_tokens, cache=None):
    shuffle(all_tokens)
    sink = None
    for token in all_tokens:
        if "sink" in token.outputs:
            sink = token
            break
    tokens = []

    if sink is None:
        return None

    connections = []
    consumed = set()

    max_depth = 10
    def fill_inputs(token, depth):
         if depth > max_depth:
            raise
         ids = []
         for input_type in token.inputs:
             target = None
             for (idx, other) in enumerate(tokens):
                if input_type in other.outputs and (idx, input_type) not in consumed:
                    consumed.add((idx, input_type))
                    target = idx
                    break
             if target is None:
                 shuffle(all_tokens)
                 for other in all_tokens:
                     if input_type in other.outputs:
                         fill_inputs(other, depth+1)
                         target = len(tokens)-1
                         consumed.add((target, input_type))
                         break
             if target is not None:
                 ids.append(target)
         connections.append(ids)
         tokens.append(token)
    try:
        fill_inputs(sink, 0)
    except:
        return None
    return Spell(tokens, connections)


def fill_shared_grimoire():
    SHARED_GRIMOIRE["small_ranged"] = [random_small_ranged() for _ in range(10)]
    SHARED_GRIMOIRE["small_bump"] = [random_small_bump() for _ in range(10)]
    SHARED_GRIMOIRE["small_heal"] = [random_small_heal() for _ in range(10)]
    SHARED_GRIMOIRE["bump_spell_free"] = Spell(
        [
            AllActors(),
            MeleeRange(),
            MadeOfPoop(),
            Small(),
            BeamOf(),
        ],
        [
            [],
            [0],
            [],
            [],
            [2, 3, 1],
        ]
    )

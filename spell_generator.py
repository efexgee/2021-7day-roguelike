from random import shuffle
from components.magic.token import all_tokens, Token
from components.magic import Spell

def random_spell_with_constraints(is_valid_fn, tokens=None):
    if tokens is None:
        tokens = [t() for t in all_tokens()]

    spell = random_spell(tokens)
    remaining_tries = 5000
    while not is_valid_fn(spell):
        if remaining_tries <= 0:
            return None
        spell = random_spell(tokens)
        remaining_tries -= 1
    return spell


def random_spell(all_tokens):
    sink = None
    shuffle(all_tokens)
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
            return False
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
                         if fill_inputs(other, depth+1):
                             target = len(tokens)-1
                             consumed.add((target, input_type))
                             break
             if target is not None:
                 ids.append(target)
         connections.append(ids)
         tokens.append(token)
         return True
    fill_inputs(sink, 0)
    return Spell(tokens, connections)

from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
import color
import actions
from components.magic.token import *

if TYPE_CHECKING:
    from entity import Item

class Context:
    def __init__(self, caster, engine):
        self.caster = caster
        self.engine = engine
        self.target = None

class Spell:
    def __init__(self, tokens, connections):
        self.tokens = tokens
        self.connections  = connections

    def __str__(self):
        return ", ".join([t.name for t in self.tokens])

    def prepare_from_inventory(self, inventory) -> Optional[PreparedSpell]:
        for token in self.tokens:
            found = False
            for item in inventory.items:
                if item.token == token and item.count > 0:
                    item.count -= 1
                    if item.count <= 0:
                        inventory.items.remove(item)
                    found = True
                    break
            if not found:
                return None
        return PreparedSpell(self)

class PreparedSpell:
    def __init__(self, spell):
        self.spell = spell

    def __str__(self):
        return ", ".join([t.name for t in self.spell.tokens])

    def cast(self, context):
        sink = None
        for (i, token) in enumerate(self.spell.tokens):
            for output in token.outputs:
                if output == "sink":
                    sink = i
                    break
            if sink is not None:
                 break

        self.cast_rec(context, sink, "sink")

    def cast_rec(self, context, token_idx, src_type):
         connections = self.spell.connections[token_idx]
         inputs = []
         for src_idx in connections:
             inputs.append(self.cast_rec(context, src_idx, src_type))
         return self.spell.tokens[token_idx].process(context, *inputs)

class Magic(BaseComponent):
    parent: Item

    def __init__(self):
        pass

    def cast_random_spell(self) -> Optional[ActionOrHandler]:
        spell = random_spell_from_inventory(self.parent.inventory)
        if spell is not None:
            context = Context(self.parent, self.engine)
            self.engine.message_log.add_message(
                "You cast a random spell", color.magic
            )
            spell.cast(context)
        else:
            self.engine.message_log.add_message(
                "You don't have the right tokens to make a spell", color.magic
            )

    def cast_spell(self, spell: Spell) -> Optional[ActionOrHandler]:
        spell = spell.prepare_from_inventory(self.parent.inventory)
        if spell is not None:
            context = Context(self.parent, self.engine)
            self.engine.message_log.add_message(
                "You cast a spell", color.magic
            )
            spell.cast(context)
        else:
            self.engine.message_log.add_message(
                "You don't have the right tokens to cast that spell", color.magic
            )

def random_spell_from_inventory(inventory: Inventory) -> PreparedSpell:
    sink = None
    for item in inventory.items:
        token = item.token 
        if not isinstance(token, Token):
            continue
        if "sink" in token.outputs:
            sink = token
            item.count -= 1
            if item.count <= 0:
                inventory.items.remove(item)
            break
    tokens = []

    if sink is None:
        return None

    connections = []
    consumed = set()

    def fill_inputs(token):
         ids = []
         for input_type in token.inputs:
             target = None
             for (idx, other) in enumerate(tokens):
                if input_type in other.outputs and (idx, input_type) not in consumed:
                    consumed.add((idx, input_type))
                    target = idx
                    break
             if target is None:
                 shuffle(inventory.items)
                 for item in inventory.items:
                     other = item.token
                     if not isinstance(other, Token):
                        continue
                     if input_type in other.outputs:
                         item.count -= 1
                         if item.count <= 0:
                            inventory.items.remove(item)
                         fill_inputs(other)
                         target = len(tokens)-1
                         consumed.add((target, input_type))
                         break
             if target is not None:
                 ids.append(target)
         connections.append(ids)
         tokens.append(token)
    fill_inputs(sink)
    return PreparedSpell(Spell(tokens, connections))

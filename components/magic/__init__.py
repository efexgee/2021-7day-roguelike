from __future__ import annotations

from random import choice

from collections import Counter

from typing import TYPE_CHECKING
import copy

from spell_inventory import SpellInventory
from components.base_component import BaseComponent
import color
import actions
from components.magic.token import *

if TYPE_CHECKING:
    from entity import Item

class Context:
    def __init__(self, caster, engine, target: Optional[(int, int)]):
        self.caster = caster
        self.engine = engine
        self.supplied_target = target
        self.attributes = dict()
        self.dry_run = False
        self.quiet = False

class Spell:
    def __init__(self, tokens, connections):
        self.tokens = tokens
        self.connections  = connections
        self.attributes = self.calculate_attributes()

    def __str__(self):
        return ", ".join([t.name for t in self.tokens])

    def needs_target(self) -> bool:
        for token in self.tokens:
            if isinstance(token, SpecificTarget):
                return True
        return False

    def calculate_attributes(self):
        context = Context(None, None, None)
        context.dry_run = True
        PreparedSpell(self).cast(context)
        return context.attributes

    def name(self):
        attributes = self.attributes
        if attributes.get("spell_shape"):
            return f"{attributes.get('scale', 'small')} {attributes.get('spell_shape')} of {attributes.get('material')}"
        elif attributes.get("is_heal"):
            return f"{attributes.get('scale', 'small')} heal"

    def can_cast(self, inventory) -> bool:
        return self.prepare_from_inventory(inventory, True) is not None

    def max_casts(self, inventory):
        needed = Counter(self.tokens);
        min_count = 10000000
        for (token, count) in needed.items():
            found = False
            for item in inventory.items:
                if item.token == token:
                    num = item.count / count
                    if num < min_count:
                        min_count = num
                    found = True
                    break
            if not found:
                 return 0
        return min_count

    def prepare_from_inventory(self, inventory, dry_run = False) -> Optional[PreparedSpell]:
        consumed = {}
        for token in self.tokens:
            found = False
            for item in inventory.items:
                if item.token == token and item.count-consumed.get(token, 0) > 0:
                    consumed[token] = consumed.get(token, 0) + 1
                    found = True
                    break
            if not found:
                return None
        if not dry_run:
            removed = []
            for item in inventory.items:
                if item.token in consumed:
                    item.count -= consumed[item.token]
                    if item.count <= 0:
                        removed.append(item)
            for item in removed:
                inventory.items.remove(item)
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
         try:
             return self.spell.tokens[token_idx].process(context, *inputs)
         except:
             print(f"Failed to process token: {self.spell.tokens[token_idx]} with inputs {inputs}")
             raise

class Magic(BaseComponent):
    parent: Item

    def __init__(self):
        self.known_tokens = set()
        self.spell_inventory = SpellInventory(self)

    def fill_default_spell_slots(self):
        from spell_generator import SHARED_GRIMOIRE
        self.spell_inventory.ranged_spell = choice(SHARED_GRIMOIRE["small_ranged"])
        self.remember_spell_tokens(self.spell_inventory.ranged_spell)

        self.spell_inventory.bump_spell = choice(SHARED_GRIMOIRE["small_bump"])
        self.remember_spell_tokens(self.spell_inventory.bump_spell)

        self.spell_inventory.heal_spell = choice(SHARED_GRIMOIRE["small_heal"])
        self.remember_spell_tokens(self.spell_inventory.heal_spell)

        self.spell_inventory.bump_spell_free = SHARED_GRIMOIRE["bump_spell_free"]

    def cast_bump_spell(self, target: Actor) -> Optional[ActionOrHandler]:
        if self.spell_inventory.bump_spell is not None:
            if self.spell_inventory.bump_spell.can_cast(self.parent.inventory):
                return self.cast_spell(self.spell_inventory.bump_spell, (target.x, target.y))
            elif self.spell_inventory.bump_spell_free:
                return self.cast_spell(self.spell_inventory.bump_spell_free, (target.x, target.y), True)

    def assure_castability(self, spell, times):
        if spell:
            for (token, count) in Counter(spell.tokens).items():
                for _ in range(times*count):
                    self.parent.inventory.add_token(token)

    def remember_spell_tokens(self, spell):
        if spell:
            self.known_tokens.update({t.__class__ for t in spell.tokens})

    def cast_spell(self, spell: Spell, target: Optional[Actor] = None, ignore_cost = False) -> Optional[ActionOrHandler]:
        if not ignore_cost and not spell.can_cast(self.parent.inventory):
            return None
        prepared_spell = None
        if not ignore_cost:
            prepared_spell = spell.prepare_from_inventory(self.parent.inventory)
        else:
            prepared_spell = PreparedSpell(spell)
        if prepared_spell is not None:
            context = Context(self.parent, self.engine, target)
            if self.parent.name == "Player":
                self.engine.message_log.add_message(
                    "You cast a spell:", color.magic
                )
            else:
                self.engine.message_log.add_message(
                    f"{self.parent.name} casts a spell:", color.magic
                )
            prepared_spell.cast(context)
        elif self.parent.name == "Player":
            self.engine.message_log.add_message(
                "You don't have the right tokens to cast that spell", color.impossible
            )
        else:
            self.engine.message_log.add_message(
                f"{self.parent.name} failed to cast a spell", color.error
            )

from __future__ import annotations

from typing import TYPE_CHECKING
import copy

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

    def __str__(self):
        return ", ".join([t.name for t in self.tokens])

    def needs_target(self) -> bool:
        for token in self.tokens:
            if isinstance(token, SpecificTarget):
                return True
        return False

    def attributes(self):
        context = Context(None, None, None)
        context.dry_run = True
        PreparedSpell(self).cast(context)
        return context.attributes

    def can_cast(self, inventory) -> bool:
        # FIXME: Um, don't copy everything?
        return self.prepare_from_inventory(copy.deepcopy(inventory)) is not None

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
        self.known_tokens = set()
        from spell_generator import random_spell_with_constraints
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
        self.ranged_spell = random_spell_with_constraints(is_valid)
        if self.ranged_spell:
            self.known_tokens.update({t.__class__ for t in self.ranged_spell.tokens})

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
        self.bump_spell = random_spell_with_constraints(is_valid)
        if self.bump_spell:
            self.known_tokens.update({t.__class__ for t in self.bump_spell.tokens})

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
        self.heal_spell = random_spell_with_constraints(is_valid)
        if self.heal_spell:
            self.known_tokens.update({t.__class__ for t in self.heal_spell.tokens})

    def cast_bump_spell(self, target: Actor) -> Optional[ActionOrHandler]:
        if self.bump_spell is not None:
            self.cast_spell(self.bump_spell, (target.x, target.y))

    def cast_spell(self, spell: Spell, target: Optional[Actor] = None) -> Optional[ActionOrHandler]:
        prepared_spell = spell.prepare_from_inventory(self.parent.inventory)
        if prepared_spell is not None:
            context = Context(self.parent, self.engine, target)
            if self.parent.name == "Player":
                self.engine.message_log.add_message(
                    "You cast a spell", color.magic
                )
            else:
                self.engine.message_log.add_message(
                    f"{self.parent.name} cast a spell", color.magic
                )
            prepared_spell.cast(context)
        elif self.parent.name == "Player":
            self.engine.message_log.add_message(
                "You don't have the right tokens to cast that spell", color.magic
            )
        else:
            self.engine.message_log.add_message(
                f"{self.parent.name} failed to cast a spell", color.magic
            )

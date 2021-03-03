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

    def cast(self, context):
        sink = None
        for (i, token) in enumerate(self.tokens):
            for output in token.outputs:
                if output == "sink":
                    sink = i
                    break
            if sink is not None:
                 break

        self.cast_rec(context, sink, "sink")

    def cast_rec(self, context, token_idx, src_type):
         connections = self.connections[token_idx]
         inputs = []
         for src_idx in connections:
             inputs.append(self.cast_rec(context, src_idx, src_type))
         return self.tokens[token_idx].process(context, *inputs)

class Magic(BaseComponent):
    parent: Item

    def __init__(self):
        tokens = [
            AllObjects(),
            OneAtRandom(),
            MadeOfWhatever("red globule", "fire"),
            BallOf()
        ]
        connections = [
            [],
            [0],
            [],
            [2, 1],
        ]
        self.current_spell = Spell(tokens, connections)

    def get_action(self, caster: Actor) -> Optional[ActionOrHandler]:
        """Try to return the action for this item."""
        return actions.ItemAction(caster, self.parent)

    def activate(self, action: actions.ItemAction) -> None:
        """Invoke this items ability.

        `action` is the context for this activation.
        """
        context = Context(self.parent, self.engine)
        self.current_spell.cast(context)

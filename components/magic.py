from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
import color
import actions

if TYPE_CHECKING:
    from entity import Item


class Magic(BaseComponent):
    parent: Item

    def __init__(self):
        pass

    def get_action(self, caster: Actor) -> Optional[ActionOrHandler]:
        """Try to return the action for this item."""
        self.engine.message_log.add_message(
            "Poop Magic!", color.needs_target
        )
        return actions.ItemAction(caster, self.parent)

    def activate(self, action: actions.ItemAction) -> None:
        """Invoke this items ability.

        `action` is the context for this activation.
        """
        self.engine.message_log.add_message(
            "Magic!", color.needs_target
        )

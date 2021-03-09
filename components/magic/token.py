from random import sample, shuffle, random, choice
import math
from inspect import signature
from spell_visualization import AOECircle, BeamLine
import entity_factories
import tile_types
from tcod.los import bresenham

import color

def all_tokens():
    tokens_with_default_constructors = []
    def class_and_descendents(c):
        ds = [c]
        for c in c.__subclasses__():
            ds.extend(class_and_descendents(c))
        return ds
    for token in class_and_descendents(Token):
        sig = signature(token)
        if len(sig.parameters) == 0:
            tokens_with_default_constructors.append(token)
    return tokens_with_default_constructors


class Token:
    def __init__(self, name, inputs, outputs):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs

    def __eq__(self, other):
        return self.name == other.name and set(self.inputs) == set(other.inputs) and set(self.outputs) == set(other.outputs)

    def __hash__(self):
        return hash((self.name, tuple(set(self.inputs)), tuple(set(self.outputs))))

    def process(self, context, *args):
        assert(False)

class AllActors(Token):
    def __init__(self):
        super().__init__("grey shard", ["caster"], ["target"])

    def process(self, context):
        if context.dry_run:
            return []
        else:
            return [(o.x, o.y) for o in context.engine.game_map.actors if o != context.caster and context.engine.game_map.visible[o.x, o.y]]

class TheCaster(Token):
    def __init__(self):
        super().__init__("black shard", ["caster"], ["target"])

    def process(self, context):
        context.attributes["targets_caster"] = True
        if context.dry_run:
            return []
        else:
            return [(context.caster.x, context.caster.y)]

class SpecificTarget(Token):
    def __init__(self):
        super().__init__("chalk shard", ["caster"], ["target"])

    def process(self, context):
        context.attributes["requires_target"] = True
        if context.supplied_target:
            return [(context.supplied_target[0], context.supplied_target[1])]
        else:
            return []

class WithinRange(Token):
    def __init__(self, range):
        super().__init__("emerald shard", ["target"], ["target"])
        self.range = range

    def process(self, context, targets):
        context.attributes["range"] = min(context.attributes.get("range", 2**32), self.range)
        if targets:
            return [t for t in targets if context.caster.distance(*t) <= self.range]
        else:
            return []

class ClosestTarget(Token):
    def __init__(self, range):
        super().__init__("jade shard", ["target"], ["target"])
        self.range = range

    def process(self, context, targets):
        if targets:
            sort(target, lambda t: context.caster.distance(*t))
            [target[0]]
        else:
            return []

class OneAtRandom(Token):
    def __init__(self):
        super().__init__("black marble", ["target"], ["target"])

    def process(self, context, targets):
        if targets:
            return sample(targets, k=1)
        else:
            return []

class MadeOfWhatever(Token):
    def __init__(self, name, material):
        self.material = material
        super().__init__(name, [], ["material"])

    def process(self, context):
        context.attributes["material"] = self.material
        return self.material

#class DoubleMaterial(Token):
#    def __init__(self):
#        super().__init__("squirming module", ["material", "material"], ["material"])
#
#    def process(self, context, a, b):
#        return f"{a} and {b}"

class Small(Token):
    def __init__(self):
        super().__init__("sighing module", [], ["scale"])

    def process(self, context):
        return "small"

class Medium(Token):
    def __init__(self):
        super().__init__("singing module", [], ["scale"])

    def process(self, context):
        return "medium"

class Large(Token):
    def __init__(self):
        super().__init__("pooping module", [], ["scale"])

    def process(self, context):
        return "large"

class Stupendous(Token):
    def __init__(self):
        super().__init__("dancing module", [], ["scale"])

    def process(self, context):
        return "stupendous"

class BallOf(Token):
    def __init__(self):
        super().__init__("silver rod", ["material", "scale", "target"], ["sink"])

    def process(self, context, material, scale, targets):
        damage = 0
        if material == "poop":
            damage = 1
        elif material == "fire":
            damage = 10
        elif material == "lightning":
            damage = 10
        elif material == "screaming elemental void":
            damage = 20
        elif material == "strong coffee":
            damage = 1
        elif material == "knives":
            damage = 5
        elif material == "ice":
            damage = 5
        elif material == "wall":
            damage = 0
        radius = 0
        if scale == "small":
            radius = 1
        elif scale == "medium":
            radius = 2
        elif scale == "large":
            radius = 4
        elif scale == "stupendous":
            radius = 12
        context.attributes["base_damage"] = damage
        context.attributes["AOE_radius"] = radius
        context.attributes["spell_shape"] = "ball"

        if context.dry_run:
            return

        if targets:
            for target in targets:
                context.engine.spell_overlay.push_effect(AOECircle(target, radius, (255, 0, 0)))
                for dx in range(-radius, radius+1):
                    for dy in range(-radius, radius+1):
                        if math.sqrt(dx*dx+dy*dy) <= radius:
                            actor = context.engine.game_map.get_actor_at_location(target[0]+dx, target[1]+dy)
                            if material == "screaming elemental void":
                                x = target[0]+dx
                                y = target[1]+dy
                                if context.engine.game_map.tiles[x, y] == tile_types.wall:
                                    context.engine.game_map.tiles[x, y] = tile_types.floor
                            if material == "wall" and actor is None:
                                context.engine.game_map.tiles[target[0]+dx, target[1]+dy] = tile_types.wall
                            elif material != "wall":
                                if actor:
                                    if not context.quiet:
                                        outcome_message = f"A {scale} ball of {material} hits {actor.name} and "
                                        outcome_message += actor.fighter.damage(damage, material)
                                        if "Player" in outcome_message and "heals" in outcome_message:
                                            context.engine.message_log.add_message(outcome_message, color.health_recovered)
                                        else:
                                            context.engine.message_log.add_message(outcome_message)
        elif not context.quiet:
            context.engine.message_log.add_message("nothing happens")

class BeamOf(Token):
    def __init__(self):
        super().__init__("copper rod", ["material", "scale", "target"], ["sink"])

    def process(self, context, material, scale, targets):
        damage = 0
        if material == "poop":
            damage = 1
        elif material == "fire":
            damage = 10
        elif material == "lightning":
            damage = 10
        elif material == "screaming elemental void":
            damage = 20
        elif material == "strong coffee":
            damage = 1
        elif material == "knives":
            damage = 5
        elif material == "ice":
            damage = 5
        elif material == "gnawing teeth":
            damage = 0.1
        elif material == "wall":
            damage = 0
        if scale == "small":
            damage *= 1
        elif scale == "medium":
            damage *= 2
        elif scale == "large":
            damage *= 4
        elif scale == "stupendous":
            damage *= 10
        context.attributes["base_damage"] = damage
        context.attributes["AOE_radius"] = 0
        context.attributes["spell_shape"] = "beam"

        if context.dry_run:
            return

        if targets:
            for target in targets:
                actor = context.engine.game_map.get_actor_at_location(target[0], target[1])
                if material == "screaming elemental void":
                    for (tx, ty) in bresenham((context.caster.x, context.caster.y), target):
                        if context.engine.game_map.tiles[tx, ty] == tile_types.wall:
                            context.engine.game_map.tiles[tx, ty] = tile_types.floor
                if actor is None and material == "wall":
                    for (tx, ty) in bresenham((context.caster.x, context.caster.y), target):
                        context.engine.game_map.tiles[tx, ty] = tile_types.wall
                elif actor is not None and material != "wall":
                    context.engine.spell_overlay.push_effect(BeamLine((context.caster.x, context.caster.y), target, (0, 0, 255)))
                    if not context.quiet:
                        outcome_message = f"A {scale} beam of {material} hits {actor.name} and "
                        outcome_message += actor.fighter.damage(damage, material)
                        if "Player" in outcome_message and "heals" in outcome_message:
                            context.engine.message_log.add_message(outcome_message, color.health_recovered)
                        else:
                            context.engine.message_log.add_message(outcome_message)
                elif not context.quiet:
                    context.engine.message_log.add_message(f"A {scale} beam of {material} hits the ground, acomplishing nothing")
        elif not context.quiet:
            context.engine.message_log.add_message("nothing happens")

class Heal(Token):
    def __init__(self):
        super().__init__("churlish rat", ["scale", "target"], ["sink"])

    def process(self, context, scale, targets):
        heal = 0
        if scale == "small":
            heal = 5
        elif scale == "medium":
            heal = 10
        elif scale == "large":
            heal = 20
        elif scale == "stupendous":
            heal = 100
        context.attributes["base_damage"] = -heal
        context.attributes["is_heal"] = True

        if context.dry_run:
            return

        if targets:
            for target in targets:
                actor = context.engine.game_map.get_actor_at_location(target[0], target[1])
                if actor is not None:
                    context.engine.spell_overlay.push_effect(AOECircle(target, 2, (0, 255, 0)))
                    if not context.quiet:
                        context.engine.message_log.add_message(
                            f"{actor.name} heals for {actor.fighter.increase_hp(heal)}!",
                            color.health_recovered
                        )
                elif not context.quiet:
                    context.engine.message_log.add_message(f"nothing happens")
        elif not context.quiet:
            context.engine.message_log.add_message("nothing happens")

class Summon(Token):
    def __init__(self):
        super().__init__("obsidian jug", ["creature", "target"], ["sink"])

    def process(self, context, creature, targets):
        context.attributes["is_summon"] = True

        if context.dry_run:
            return

        if targets:
            for target in targets:
                count = 0
                for c in creature[1]():
                    drop_targets = []
                    for dx in range(-1, 2):
                        for dy in range(-1, 2):
                            x = target[0] + dx
                            y = target[1] + dy
                            if x >= 0 and x < context.engine.game_map.width and y >= 0 and y < context.engine.game_map.height and context.engine.game_map.tiles["walkable"][x,y]:
                                if not context.engine.game_map.get_blocking_entity_at_location(x,y):
                                    drop_targets.append((x,y))
                    if drop_targets:
                        target = choice(drop_targets)
                        context.engine.spell_overlay.push_effect(AOECircle(target, 2, (0, 0, 255)))
                        c.spawn(context.engine.game_map, target[0], target[1])
                        count += 1
                if count > 0:
                    if not context.quiet:
                        if count > 1:
                            context.engine.message_log.add_message(
                                f"{count} {creature[0]}s appear",
                                color.player_atk
                            )
                        else:
                            context.engine.message_log.add_message(
                                f"a {creature[0]} appears",
                                color.player_atk
                            )
                    elif not context.quiet:
                        context.engine.message_log.add_message(f"nothing happens")
                elif not context.quiet:
                    context.engine.message_log.add_message("nothing happens")
        elif not context.quiet:
            context.engine.message_log.add_message("nothing happens")

class Creature(Token):
    def __init__(self, name, creature_name, creature_fn):
        super().__init__(name, [], ["creature"])
        self.creature_name = creature_name
        self.creature_fn = creature_fn

    def process(self, context):
        context.attributes["creature"] = self.creature_name
        return (self.creature_name, self.creature_fn)

class Squirrel(Creature):
    def __init__(self):
        super().__init__("flint needle", "squirrel", entity_factories.squirrel)

class MeleeRange(WithinRange):
    def __init__(self):
        super().__init__(1.5)
class CloseRange(WithinRange):
    def __init__(self):
        super().__init__(4)
class LongRange(WithinRange):
    def __init__(self):
        super().__init__(10)

class MadeOfPoop(MadeOfWhatever):
    def __init__(self):
        super().__init__("red globule", "poop")
class MadeOfFire(MadeOfWhatever):
    def __init__(self):
        super().__init__("green globule", "fire")
class MadeOfIce(MadeOfWhatever):
    def __init__(self):
        super().__init__("black globule", "ice")
class MadeOfLightning(MadeOfWhatever):
    def __init__(self):
        super().__init__("puce globule", "lightning")
class MadeOfKnives(MadeOfWhatever):
    def __init__(self):
        super().__init__("steely globule", "knives")
class MadeOfStrongCoffee(MadeOfWhatever):
    def __init__(self):
        super().__init__("blue globule", "strong coffee")
class MadeOfScreamingElementalVoid(MadeOfWhatever):
    def __init__(self):
        super().__init__("pink globule", "screaming elemental void")

class MadeOfWall(MadeOfWhatever):
    def __init__(self):
        super().__init__("dusty globule", "wall")

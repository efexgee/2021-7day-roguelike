from random import sample, shuffle, random

class Token:
    def __init__(self, name, inputs, outputs):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs

    def __eq__(self, other):
        return self.name == other.name and set(self.inputs) == set(other.inputs) and set(self.outputs) == set(other.outputs)

    def process(self, context, *args):
        assert(False)

class AllActors(Token):
    def __init__(self):
        super().__init__("grey shard", ["caster"], ["target"])

    def process(self, context):
        return [(o.x, o.y) for o in context.engine.game_map.actors if o != context.caster and context.engine.game_map.visible[o.x, o.y]]

class TheCaster(Token):
    def __init__(self):
        super().__init__("black shard", ["caster"], ["target"])

    def process(self, context):
        return [(context.caster.x, context.castor.y)]

class SpecificTarget(Token):
    def __init__(self):
        super().__init__("chalk shard", ["caster"], ["target"])

    def process(self, context):
        if context.supplied_target:
            return [(context.supplied_target[0], context.supplied_target[1])]
        else:
            return []

class WithinRange(Token):
    def __init__(self, range):
        super().__init__("emerald shard", ["target"], ["target"])
        self.range = range

    def process(self, context, targets):
        if targets:
            return [t for t in targets if context.caster.distance(*t) < self.range]
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
        return self.material

class DoubleMaterial(Token):
    def __init__(self):
        super().__init__("squirming module", ["material", "material"], ["material"])

    def process(self, context, a, b):
        return f"{a} and {b}"

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
        if targets:
            damage = 0
            if material == "poop":
                damage = 1
            elif material == "fire":
                damage = 10
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
            for target in targets:
                for actor in context.engine.game_map.actors:
                    if actor.distance(target[0], target[1]) <= radius and context.engine.game_map.visible[target]:
                        if not context.dry_run:
                            context.engine.message_log.add_message(f"A {scale} ball of {material} hits {actor.name} dealing {damage} damage!")
                            actor.fighter.take_damage(damage)
        elif not context.dry_run:
            context.engine.message_log.add_message("nothing happens")

class BeamOf(Token):
    def __init__(self):
        super().__init__("copper rod", ["material", "scale", "target"], ["sink"])

    def process(self, context, material, scale, targets):
        if targets:
            damage = 0
            if material == "poop":
                damage = 1
            elif material == "fire":
                damage = 10
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
            for target in targets:
                actor = context.engine.game_map.get_actor_at_location(target[0], target[1])
                if actor is not None:
                    if not context.dry_run:
                        context.engine.message_log.add_message(f"A {scale} beam of {material} hits {actor.name} dealing {damage} damage!")
                        actor.fighter.take_damage(damage)
                elif not context.dry_run:
                    context.engine.message_log.add_message(f"A {scale} beam of {material} hits the ground, acomplishing nothing")
        elif not context.dry_run:
            context.engine.message_log.add_message("nothing happens")

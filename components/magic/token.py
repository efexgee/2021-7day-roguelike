from random import sample, shuffle, random

class Token:
    def __init__(self, name, inputs, outputs):
        self.name = name
        self.inputs = inputs
        self.outputs = outputs

    def process(self, context, *args):
        assert(False)

class AllObjects(Token):
    def __init__(self):
        super().__init__("grey shard", ["caster"], ["target"])

    def process(self, context):
        return [o for o in context.engine.game_map.actors if o != context.caster]

class TheCaster(Token):
    def __init__(self):
        super().__init__("black shard", ["caster"], ["target"])

    def process(self, context):
        return [context.caster]

class SpecificTarget(Token):
    def __init__(self):
        super().__init__("chalk shard", ["caster"], ["target"])

    def process(self, context):
        if context.target:
            return [context.target]
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

class JustOrcs(Token):
    def __init__(self):
        super().__init__("green marble", ["target"], ["target"])

    def process(self, context, targets):
        return [t for t in targets if "Orc" in t.name]

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


class BallOf(Token):
    def __init__(self):
        super().__init__("silver rod", ["material", "target"], ["sink"])

    def process(self, context, material, targets):
        if targets:
            damage = 0
            if material == "poop":
                damage = 1
            elif material == "fire":
                damage = 10
            for target in targets:
                context.engine.message_log.add_message(f"A ball of {material} hits {target.name} dealing {damage} damage!")
                target.fighter.take_damage(damage)
        else:
            context.engine.message_log.add_message("nothing happens")

class BeamOf(Token):
    def __init__(self):
        super().__init__("copper rod", ["material", "target"], ["sink"])

    def process(self, context, material, targets):
        if targets:
            for target in targets:
                context.engine.message_log.add_message(f"A beam of {material} hits {target.name}")
        else:
            context.engine.message_log.add_message("nothing happens")

#class Age(Token):
#    def __init__(self, name, age):
#        self.age = age
#        super().__init__(name, [], ["age"])
#
#    def process(self, context):
#        return self.age
#
#class Animal(Token):
#    def __init__(self, name, animal):
#        self.animal = animal
#        super().__init__(name, [], ["animal"])
#
#    def process(self, context):
#        return self.animal
#
#class SummonableAnimal(Token):
#    def __init__(self):
#        super().__init__("dusty stone", ["animal", "age"], ["summonable"])
#
#    def process(self, context, animal, age):
#        return f"{age} {animal}"
#
#class Summon(Token):
#    def __init__(self):
#        super().__init__("chrome ring", ["target", "summonable"], ["sink"])
#
#    def process(self, context, targets, summonable):
#        for target in targets:
#            context.world.objects.append(summonable)
#            context.engine.message_log.add_message(f"{context.caster} summon a {summonable} near a {target}");

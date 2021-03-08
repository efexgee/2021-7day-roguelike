import math
from tcod.los import bresenham

class SpellVisualEffect:
    def on_render(sel, console, engine):
        return False

class AOECircle(SpellVisualEffect):
    def __init__(self, target, radius, color):
        self.target = target
        self.radius = radius
        self.color = color

    def on_render(self, console, engine):
        (x, y) = self.target
        did_render = False
        for dx in range(-self.radius, self.radius+1):
            for dy in range(-self.radius, self.radius+1):
                if math.sqrt(dx ** 2 + dy ** 2) < self.radius:
                    tx = x+dx
                    ty = y+dy
                    if tx >= 0 and tx < console.width and ty >= 0 and ty < console.height:
                        if engine.game_map.visible[tx, ty]:
                            did_render = True
                            # TODO: Presumably there's a better way to do blending
                            console.bg[tx, ty, 0] = max(0, min(255, console.bg[tx, ty, 0]+self.color[0]))
                            console.bg[tx, ty, 1] = max(0, min(255, console.bg[tx, ty, 1]+self.color[1]))
                            console.bg[tx, ty, 2] = max(0, min(255, console.bg[tx, ty, 2]+self.color[2]))
        return did_render

class BeamLine(SpellVisualEffect):
    def __init__(self, source, target, color):
        self.source = source
        self.target = target
        self.color = color

    def on_render(self, console, engine):
        did_render = False
        for (tx,ty) in bresenham(self.source, self.target):
            if engine.game_map.visible[tx, ty]:
                did_render = True
                console.bg[tx, ty, 0] = max(0, min(255, console.bg[tx, ty, 0]+self.color[0]))
                console.bg[tx, ty, 1] = max(0, min(255, console.bg[tx, ty, 1]+self.color[1]))
                console.bg[tx, ty, 2] = max(0, min(255, console.bg[tx, ty, 2]+self.color[2]))
        return did_render

class SpellVisualizationOverlay:
    def __init__(self, engine):
        self.active_effects = []
        self.engine = engine

    def on_render(self, console):
        did_render = False
        for effect in self.active_effects:
            did_render |= effect.on_render(console, self.engine)
        self.active_effects.clear()
        return did_render

    def push_effect(self, effect):
        self.active_effects.append(effect)

import numpy as np
import tcod

class PathingCache:
    def __init__(self, engine):
        self.engine = engine

        self.token_flow = None
        self.player_flow = None
        self.anti_player_flow = None
        self.random_flow = None
        self.mushroom_flow = None

    def update_flow_maps(self):
        self.update_token_flow()
        self.update_player_flow()
        self.update_anti_player_flow()
        self.update_random_flow()
        self.update_mushroom_flow()


    def default_cost(self):
        cost = np.array(self.engine.game_map.tiles["walkable"], dtype=np.int16)
        cost += self.engine.game_map.tiles["damage"] * 10
        return cost

    def update_token_flow(self):
        cost = self.default_cost()
        dist = np.full(cost.shape, 1000)
        for entity in self.engine.game_map.items:
            dist[entity.x, entity.y] = 0
        for entity in self.engine.game_map.actors:
            cost[entity.x, entity.y] = 1000
            dist[entity.x, entity.y] = 50
        tcod.path.dijkstra2d(dist, cost, 2, 3)
        self.token_flow = dist

    def update_player_flow(self):
        cost = self.default_cost()
        dist = np.full(cost.shape, 1000)
        for entity in self.engine.game_map.actors:
            if entity is not self.engine.player:
                cost[entity.x, entity.y] = 1000
                dist[entity.x, entity.y] = 50
        dist[self.engine.player.x, self.engine.player.y] = 0
        tcod.path.dijkstra2d(dist, cost, 2, 3)
        self.player_flow = dist

    def update_anti_player_flow(self):
        cost = self.default_cost()
        dist = np.full(cost.shape, 100000)

        for entity in self.engine.game_map.actors:
            if entity is not self.engine.player:
                cost[entity.x, entity.y] = 1000
        dist[self.engine.player.x, self.engine.player.y] = 0
        tcod.path.dijkstra2d(dist, cost, 2, 3)
        self.anti_player_flow = (dist * np.where(dist < 10000, -1, 1))*dist

    def update_mushroom_flow(self):
        cost = self.default_cost()
        dist = np.full(cost.shape, 100000)
        for entity in self.engine.game_map.actors:
            if entity.name == "Mushroom":
                dist[entity.x, entity.y] = 0
        tcod.path.dijkstra2d(dist, cost, 2, 3)
        self.mushroom_flow = dist

    def update_random_flow(self):
        cost = self.default_cost()
        dist = (np.random.rand(*cost.shape) * 100 - 200).astype(np.int16)
        tcod.path.dijkstra2d(dist, cost, 2, 3)
        self.random_flow = dist

    def path_along_flow(self, flow, x, y):
        path = tcod.path.hillclimb2d(flow, (x, y), True, True)[1:].tolist()
        return [(index[0], index[1]) for index in path]

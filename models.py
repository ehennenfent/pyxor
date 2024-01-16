from typing import List, Tuple

from pydantic import BaseModel


class Position(BaseModel):
    x: int
    y: int

    def distance(self, other: "Position") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


class Fleet(BaseModel):
    owner: str
    count: int


class MovingFleet(BaseModel):
    fleet: Fleet
    ticks_til: int
    travel_time: int
    goal: int
    origin: int


class System(BaseModel):
    id: int
    economy: int
    owner: str
    fleets: List[Fleet]
    upgrade_left: int
    pos: Position

    def enemy_strengh(self, player: str) -> int:
        return sum(f.count for f in self.fleets if f.owner != player)

    def player_strengh(self, player: str) -> int:
        return sum(f.count for f in self.fleets if f.owner == player)


class GameStats(BaseModel):
    ship_cnt: List[Tuple[str, int]]
    system_cnt: List[Tuple[str, int]]


class GameData(BaseModel):
    tick: int
    players: List[str]
    systems: List[System]
    fleets: List[MovingFleet]
    stats: GameStats

    def player_presence_systems(self, player: str):
        yield from self.systems_where(lambda s: any(f.owner == player for f in s.fleets))

    def player_owned(self, player: str):
        yield from self.systems_where(lambda s: s.owner == player)

    def player_dominated(self, player: str):
        yield from self.systems_where(lambda s: s.player_strengh(player) > s.enemy_strengh(player) * 3)

    def systems_where(self, predicate):
        for system in self.systems:
            if predicate(system):
                yield system

    def for_player(self, player: str) -> "GameData":
        return GameData(
            tick=self.tick,
            players=[p for p in self.players if p == player],
            systems=[s for s in self.player_presence_systems(player)],
            fleets=[f for f in self.fleets if f.fleet.owner == player],
            stats=GameStats(
                ship_cnt=[(player, cnt) for player, cnt in self.stats.ship_cnt if player == player],
                system_cnt=[(player, cnt) for player, cnt in self.stats.system_cnt if player == player],
            ),
        )

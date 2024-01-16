from math import sqrt
from random import choice, sample

from models import GameData, GameStats, System
from websockets.exceptions import ConnectionClosedError
from websockets.sync.client import connect

HOST = "ws://calliope:9091"
ME = "PLAYER"
MAX_TARGETS = 3
STRENGTH_MARGIN = 1.1
MOVES_PER_TICK = 10


def plan_move(this_system: System, game_data: GameData) -> str | None:
    my_strength = this_system.player_strengh(ME)
    commit_strength = my_strength // 2

    viable_targets = []
    for system in sorted(
        game_data.systems, key=lambda s: (s.pos.distance(this_system.pos) * sqrt(s.enemy_strengh(ME)))
    ):
        enemy_strength = system.enemy_strengh(ME)
        too_weak = enemy_strength > commit_strength
        my_system = system.player_strengh(ME) > enemy_strength
        is_this_system = system.id == this_system.id

        if not too_weak and not my_system and not is_this_system:
            viable_targets.append(system)
        if len(viable_targets) >= MAX_TARGETS:
            break

    if viable_targets:
        target = choice(viable_targets)
        committed_strength = min(int(target.enemy_strengh(ME) * STRENGTH_MARGIN), commit_strength)
        if committed_strength > 0:
            return f"MOV {ME} {this_system.id} {target.id} {committed_strength}"

    return None


def main():
    with connect(HOST) as websocket:
        while True:
            last_tick = -1
            try:
                game_data = GameData.model_validate_json(websocket.recv())
                if game_data.tick != last_tick:
                    last_tick = game_data.tick
                    moves = [
                        mv
                        for system in game_data.player_dominated(ME)
                        if (mv := plan_move(system, game_data)) is not None
                    ]
                    for mv in sample(moves, min(len(moves), MOVES_PER_TICK)):
                        websocket.send(mv)
            except ConnectionClosedError:
                print("connection closed")
                websocket.close()
                break
            except KeyboardInterrupt:
                print("caught ctrl+c")
                websocket.close()
                break


if __name__ == "__main__":
    main()

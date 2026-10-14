# CMPUT 455 Assignment 2 starter code
# This is a sample solution for assignment 1.
# Implement the new commands to complete the assignment
# Full assignment specification and game rules on Canvas

import ast
import random
from sys import stderr
from typing import Any, Callable, Dict, List, Optional, Tuple
import time

class SearchTimeout(Exception):
    pass

# ---------------------------------------------------------------------------
# Assignment restrictions (see assignment page)
# ---------------------------------------------------------------------------
MIN_HEAPS = 1
MAX_HEAPS = 20
MIN_TOKENS = 1
MAX_TOKENS = 20
MIN_VALUE = 1
MAX_VALUE = 20
KOMI_LIMIT = 100  # -100 < komi < 100, and komi must be an integer + 0.5

# The time limit, in seconds, for a single solve or genmove command
MIN_TIMELIMIT = 1
MAX_TIMELIMIT = 100
DEFAULT_TIMELIMIT = 1

BLACK = 'b'
WHITE = 'w'
COLORS = (BLACK, WHITE)

Token = Tuple[str, int]
Heap = List[Token]
Heaps = List[Heap]


def not_yet() -> bool:
    raise NotImplementedError("Command not implemented.")
    return False


def print_error(error: str) -> None:
    print(error, file=stderr)


def opponent(color: str) -> str:
    return WHITE if color == BLACK else BLACK

def simulate_move(heaps, heights, player, move):
    heap = heaps[move]
    height = heights[move]
    gained = 0

    # Take player's own color tokens
    while height > 0 and heap[height - 1][0] == player:
        gained += heap[height - 1][1]
        height -= 1
    #take the first opponent's token after player getting its own tokens
    if height > 0:
        gained += heap[height - 1][1]
        height -= 1

    new_heights = list(heights)
    new_heights[move] = height

    return tuple(new_heights), gained
# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
def is_int(obj: Any) -> bool:
    # bool is a subclass of int; True/False are not valid values
    return isinstance(obj, int) and not isinstance(obj, bool)


def is_token(obj: Any) -> bool:
    return (isinstance(obj, tuple)
            and len(obj) == 2
            and obj[0] in COLORS
            and is_int(obj[1])
            and MIN_VALUE <= obj[1] <= MAX_VALUE)


def is_heap(obj: Any) -> bool:
    return (isinstance(obj, list)
            and MIN_TOKENS <= len(obj) <= MAX_TOKENS
            and all(is_token(token) for token in obj))


def is_heaps(obj: Any) -> bool:
    return (isinstance(obj, list)
            and MIN_HEAPS <= len(obj) <= MAX_HEAPS
            and all(is_heap(heap) for heap in obj))


def parse_komi(text: str) -> Optional[float]:
    try:
        komi = float(text)
    except ValueError:
        return None
    if not (-KOMI_LIMIT < komi < KOMI_LIMIT):
        return None
    if (komi - 0.5) != int(komi - 0.5):
        return None
    return komi


def parse_heaps(text: str) -> Optional[Heaps]:
    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return None
    if not is_heaps(parsed):
        return None
    return parsed


def parse_heap_number(args: str) -> Optional[int]:
    parts = args.split()
    if len(parts) != 1:
        return None
    try:
        return int(parts[0])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class HeapGo:
    def __init__(self, komi: float, heaps: Heaps) -> None:
        self.komi = komi
        self.heaps = heaps
        self.toplay = BLACK
        self.score = {BLACK: 0, WHITE: komi}

    def __str__(self) -> str:
        return "k {} {}".format(self.komi, self.heaps)

    def is_legal(self, heap_number: int) -> bool:
        return 0 <= heap_number < len(self.heaps) and len(self.heaps[heap_number]) > 0

    def legal_moves(self) -> List[int]:
        return [i for i in range(len(self.heaps)) if self.is_legal(i)]

    def game_over(self) -> bool:
        return len(self.legal_moves()) == 0

    def play(self, heap_number: int) -> bool:
        if not self.is_legal(heap_number):
            return False
        heap = self.heaps[heap_number]
        gained = 0
        # Rule 1: take all own-color tokens from the top
        while heap and heap[-1][0] == self.toplay:
            gained += heap.pop()[1]
        # Rule 2: then one opponent token, if any remain
        if heap:
            gained += heap.pop()[1]
        self.score[self.toplay] += gained
        self.toplay = opponent(self.toplay)
        return True

    def winner(self) -> Optional[str]:
        if not self.game_over():
            return None
        if self.score[BLACK] > self.score[WHITE]:
            return BLACK
        if self.score[WHITE] > self.score[BLACK]:
            return WHITE
        return None  # draw; impossible with komi = integer + 0.5


CommandMap = Dict[str, Callable[[str], bool]]


class CommandInterface:
    def __init__(self) -> None:
        self.game: Optional[HeapGo] = None
        self.timelimit = DEFAULT_TIMELIMIT
        # you can add your own initialisation here
        self.commands: CommandMap = {
            "help": self.cmd_help,
            "heapgo": self.cmd_heapgo,
            "show": self.cmd_show,
            "toplay": self.cmd_toplay,
            "play": self.cmd_play,
            "legal": self.cmd_legal,
            "genmove": self.cmd_genmove,
            "score": self.cmd_score,
            "winner": self.cmd_winner,
            "solve": self.cmd_solve,
            "timelimit": self.cmd_timelimit,
            }

#============================================================================
# Command implementations
#============================================================================
    def cmd_heapgo(self, args: str) -> bool:
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            print_error("usage: heapgo komi game")
            return False
        komi = parse_komi(parts[0])
        if komi is None:
            print_error("invalid komi: {}".format(parts[0]))
            return False
        heaps = parse_heaps(parts[1])
        if heaps is None:
            print_error("invalid game: {}".format(parts[1]))
            return False
        self.game = HeapGo(komi, heaps)
        return True

    def cmd_show(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        print(self.game)
        return True

    def cmd_toplay(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        if args not in COLORS:
            print_error("invalid color: {}".format(args))
            return False
        self.game.toplay = args
        return True

    def cmd_play(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        heap_number = parse_heap_number(args)
        if heap_number is None:
            print_error("invalid heap number: {}".format(args))
            return False
        if not self.game.play(heap_number):
            print_error("illegal move: {}".format(heap_number))
            return False
        return True

    def cmd_legal(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        heap_number = parse_heap_number(args)
        if heap_number is None:
            print_error("invalid heap number: {}".format(args))
            return False
        print("yes" if self.game.is_legal(heap_number) else "no")
        return True

    def gen_randmove(self):
        moves = self.game.legal_moves()
        if not moves:
            return None

        return random.choice(moves)

    def cmd_genmove(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False

        res = self.solve()
        if res is None:
            move = self.gen_randmove()
        else:
            colour, move = res
            if colour != self.game.toplay:
                move = self.gen_randmove()

        if move is None:
            print_error("no legal moves")
            return False

        self.game.play(move)
        print(move)
        return True

    def cmd_score(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        print("b {} w {}".format(self.game.score[BLACK], self.game.score[WHITE]))
        return True

    def cmd_winner(self, args: str) -> bool:
        if self.game is None:
            print_error("no game started")
            return False
        winner = self.game.winner()
        if winner is None:
            print_error("game not over" if not self.game.game_over() else "draw")
            return False
        print(winner)
        return True

#============================================================================
# You need to implement the following methods.
#============================================================================
    def cmd_solve(self, args: str) -> bool:
        result = self.solve()

        if result is None:
            return False

        winner, move = result

        if winner == self.game.toplay:
            print(winner, move)
        else:
            print(winner)

        return True

    def cmd_timelimit(self, args: str) -> bool:
        try:
            s = int(args)
            if s not in range(1,101):
                raise ValueError()
        except ValueError:
            print_error("invalid timelimit")
            return False
        self.timelimit = s
        return True
#============================================================================
# End of functions requiring implementation
#============================================================================
    def solve(self):
        """
        The actual solver:

        Returns a tuple of (colour, move) if it reaches a solution
            move is for game.to_play (whether winning or losing)
        Returns None if it times out
        """
        game = self.game

        heaps = game.heaps
        heights = tuple(len(heap) for heap in heaps)

        player = game.toplay
        score_diff = game.score['b'] - game.score['w']

        deadline = time.monotonic() + self.timelimit
        cache = {}

        #compute remaining token values
        prefix = []
        for heap in heaps:
            sums = [0]
            for color, value in heap:
                sums.append(sums[-1] + value)
            prefix.append(sums)

        def minimax(heights, player, score_diff):
            # Check timelimit
            if time.monotonic() >= deadline:
                raise SearchTimeout()

            # Base case
            if all(height == 0 for height in heights):
                if score_diff > 0:
                    return 'b', None
                else:
                    return 'w', None

            remaining = 0
            for i in range(len(heights)):
                remaining += prefix[i][heights[i]]

            if score_diff > remaining:
                winner = 'b'
            elif score_diff + remaining < 0:
                winner = 'w'
            else:
                winner = None

            if winner is not None:
                if winner == player:
                    for move in range(len(heights)):
                        if heights[move] > 0:
                            return winner, move

                return winner, None

            # Transposition table lookup
            state = (heights, player, score_diff)

            if state in cache:
                return cache[state]

            moves = []

            for move in range(len(heights)):
                if heights[move] == 0:
                    continue

                new_heights, gained = simulate_move(
                    heaps, heights, player, move
                )

                moves.append((gained, move, new_heights))

            moves.sort(reverse=True)

            for gained, move, new_heights in moves:

                # Score difference
                if player == 'b':
                    new_diff = score_diff + gained
                else:
                    new_diff = score_diff - gained

                next_player = opponent(player)

                winner, _ = minimax(
                    new_heights,
                    next_player,
                    new_diff
                )

                # Found a winning move
                if winner == player:
                    result = (player, move)
                    cache[state] = result
                    return result

            # Every legal move loses
            result = (opponent(player), None)
            cache[state] = result
            return result

        try:
            result = minimax(heights, player, score_diff)

            # Verify deadline before returning
            if time.monotonic() >= deadline:
                return None

            return result

        except SearchTimeout:
            return None

#============================================================================
# The code below should not need modification
# Anyway, you may change or add to this code as you see fit
#============================================================================
    def cmd_help(self, ignore_args: str) -> bool:
        print("\nKnown commands:")
        for cmd in self.commands:
            print(cmd)
        return True

    def process_command(self, cmd_name: str, cmd_args: str) -> None:
        status = "= -1"
        cmd = self.commands.get(cmd_name)
        if cmd:
            try:
                if cmd(cmd_args):
                    status = "= 1"
            except Exception as e:
                print_error(f"Command {cmd_name} with arguments {cmd_args} failed with exception: {e}")
        else:
            print_error("Unknown command. Type 'help' for commands.")
        print(status)

    def main_loop(self) -> None:
        process_commands = True
        while process_commands:
            try:
                line = input()
            except EOFError:
                break
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            cmd_name = parts[0]
            if cmd_name == "exit":
                process_commands = False
                continue
            cmd_args = parts[1] if len(parts) > 1 else ""
            self.process_command(cmd_name, cmd_args)


if __name__ == "__main__":
    interface = CommandInterface()
    interface.main_loop()

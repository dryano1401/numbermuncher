"""Game logic for a Number Munchers clone (no Streamlit imports, easy to test)."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

ROWS, COLS = 5, 6
START_LIVES = 3
POINTS_PER_MUNCH = 10


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


# ---------------------------------------------------------------- rules
@dataclass
class Rule:
    kind: str          # multiples | factors | primes | equals | less | greater
    n: int = 0         # parameter for the rule (unused for primes)

    @property
    def title(self) -> str:
        return {
            "multiples": f"MULTIPLES OF {self.n}",
            "factors": f"FACTORS OF {self.n}",
            "primes": "PRIME NUMBERS",
            "equals": f"EQUALS {self.n}",
            "less": f"LESS THAN {self.n}",
            "greater": f"GREATER THAN {self.n}",
        }[self.kind]

    def matches(self, value) -> bool:
        if self.kind == "multiples":
            return value % self.n == 0
        if self.kind == "factors":
            return self.n % value == 0
        if self.kind == "primes":
            return is_prime(value)
        if self.kind == "equals":
            return value == self.n
        if self.kind == "less":
            return value < self.n
        if self.kind == "greater":
            return value > self.n
        raise ValueError(self.kind)

    # -- cell generation -------------------------------------------------
    def correct_value(self, rng: random.Random):
        k = self.kind
        if k == "multiples":
            return self.n * rng.randint(1, max(2, 99 // self.n))
        if k == "factors":
            return rng.choice([d for d in range(1, self.n + 1) if self.n % d == 0])
        if k == "primes":
            return rng.choice([p for p in range(2, 60) if is_prime(p)])
        if k == "equals":
            return self.n
        if k == "less":
            return rng.randint(1, self.n - 1)
        return rng.randint(self.n + 1, self.n + 40)

    def wrong_value(self, rng: random.Random):
        for _ in range(200):
            if self.kind in ("multiples", "primes"):
                v = rng.randint(2, 99)
            elif self.kind == "factors":
                v = rng.randint(2, max(12, self.n + 6))
            elif self.kind == "equals":
                v = rng.randint(max(1, self.n - 8), self.n + 8)
            else:
                v = rng.randint(max(1, self.n - 25), self.n + 25)
            if not self.matches(v):
                return v
        return 1000

    def random_value(self, rng: random.Random):
        """Value for a refilled cell: roughly 40% correct."""
        return self.correct_value(rng) if rng.random() < 0.4 else self.wrong_value(rng)


def _equals_expr(target: int, rng: random.Random) -> str:
    """Expression whose value is `target`, shown for the Equals rule."""
    op = rng.choice("+-*")
    if op == "+" and target >= 2:
        a = rng.randint(1, target - 1)
        return f"{a}+{target - a}"
    if op == "-":
        b = rng.randint(1, 9)
        return f"{target + b}-{b}"
    divs = [d for d in range(2, target + 1) if target % d == 0 and d != target]
    if divs:
        d = rng.choice(divs)
        return f"{d}*{target // d}"
    return f"{target + 1}-1"


class EqualsRule(Rule):
    """Cells hold expressions (strings); the rule evaluates them."""

    def matches(self, value) -> bool:
        return eval(value, {"__builtins__": {}}) == self.n  # only our own strings

    def correct_value(self, rng):
        return _equals_expr(self.n, rng)

    def wrong_value(self, rng):
        for _ in range(100):
            t = rng.randint(max(1, self.n - 9), self.n + 9)
            if t != self.n:
                return _equals_expr(t, rng)
        return _equals_expr(self.n + 1, rng)


def make_rule(level: int, rng: random.Random) -> Rule:
    kinds = ["multiples", "factors", "primes", "equals", "less", "greater"]
    kind = rng.choice(kinds)
    hard = min(level, 8)
    if kind == "multiples":
        return Rule(kind, rng.randint(2, 4 + hard))
    if kind == "factors":
        return Rule(kind, rng.choice([12, 18, 20, 24, 30, 36, 40, 48, 60][: 4 + hard]))
    if kind == "primes":
        return Rule(kind)
    if kind == "equals":
        return EqualsRule(kind, rng.randint(6, 12 + hard * 2))
    if kind == "less":
        return Rule(kind, rng.randint(15, 40))
    return Rule(kind, rng.randint(15, 40))


# ---------------------------------------------------------------- state
@dataclass
class Troggle:
    r: int
    c: int
    name: str = "Reggie"
    skill: float = 0.5  # chance of chasing the muncher rather than wandering


# Sound cue priorities: when several things happen in one action, the loudest wins.
SOUND_PRIORITY = {"": 0, "step": 1, "troggle": 2, "nope": 2, "start": 3, "munch": 3,
                  "oops": 4, "caught": 5, "level": 6, "gameover": 7}

TROGGLE_NAMES = ["Reggie", "Bashful", "Helper", "Worker", "Fripp"]


@dataclass
class Game:
    seed: int | None = None
    level: int = 1
    score: int = 0
    lives: int = START_LIVES
    turn: int = 0
    message: str = ""
    over: bool = False
    rule: Rule = field(default=None)
    grid: list = field(default_factory=list)
    pr: int = ROWS // 2
    pc: int = COLS // 2
    troggles: list = field(default_factory=list)
    rng: random.Random = field(default=None)
    flash: str = ""  # "", "good", "bad", "caught"
    sound: str = "start"  # cue name for the UI to play after the latest action
    sound_seq: int = 1    # bumps every action so the UI plays each cue exactly once

    def __post_init__(self):
        self.rng = random.Random(self.seed)
        self.start_level()

    # -- sound cues -----------------------------------------------------
    def _begin(self, cue: str):
        self.sound, self.sound_seq = cue, self.sound_seq + 1

    def _snd(self, cue: str):
        if SOUND_PRIORITY[cue] >= SOUND_PRIORITY[self.sound]:
            self.sound = cue

    # -- level setup --------------------------------------------------
    def start_level(self):
        self.rule = make_rule(self.level, self.rng)
        self.grid = [[self.rule.random_value(self.rng) for _ in range(COLS)] for _ in range(ROWS)]
        # guarantee a reasonable number of correct answers
        while self.remaining() < 6:
            r, c = self.rng.randrange(ROWS), self.rng.randrange(COLS)
            self.grid[r][c] = self.rule.correct_value(self.rng)
        self.pr, self.pc = ROWS // 2, COLS // 2
        self.grid[self.pr][self.pc] = None
        self.troggles = []
        self.turn = 0
        self.flash = ""
        self.message = f"EAT {self.rule.title}"

    def remaining(self) -> int:
        return sum(
            1 for row in self.grid for v in row if v is not None and self.rule.matches(v)
        )

    # -- actions ------------------------------------------------------
    def move(self, dr: int, dc: int):
        if self.over:
            return
        self.flash = ""
        self._begin("step")
        self.message = f"EAT {self.rule.title}"
        nr, nc = self.pr + dr, self.pc + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            self.pr, self.pc = nr, nc
        self._end_turn()

    def munch(self):
        if self.over:
            return
        self.flash = ""
        self._begin("")
        v = self.grid[self.pr][self.pc]
        if v is None:
            self._snd("nope")
            self.message = "NOTHING HERE TO MUNCH"
            self._end_turn()
            return
        if self.rule.matches(v):
            self.grid[self.pr][self.pc] = None
            self.score += POINTS_PER_MUNCH
            self.flash = "good"
            self._snd("munch")
            self.message = f"YUM! {v}"
            if self.remaining() == 0:
                self.level += 1
                self.score += 50
                self.start_level()
                self.message = f"LEVEL {self.level - 1} CLEARED! +50  |  EAT {self.rule.title}"
                self.flash = "level"
                self._snd("level")
                return
        else:
            self.flash = "bad"
            self._snd("oops")
            self.message = f"OOPS! {v} IS NOT {self.rule.title}"
            self.grid[self.pr][self.pc] = None
            self._lose_life()
        self._end_turn()

    # -- internals ----------------------------------------------------
    def _lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.over = True
            self._snd("gameover")
            self.message = "GAME OVER"
        else:
            self.pr, self.pc = ROWS // 2, COLS // 2
            self.troggles = []

    def _spawn_troggle(self):
        if len(self.troggles) >= min(1 + self.level // 2, 4):
            return
        side = self.rng.choice("LRTB")
        if side == "L":
            r, c = self.rng.randrange(ROWS), 0
        elif side == "R":
            r, c = self.rng.randrange(ROWS), COLS - 1
        elif side == "T":
            r, c = 0, self.rng.randrange(COLS)
        else:
            r, c = ROWS - 1, self.rng.randrange(COLS)
        if (r, c) == (self.pr, self.pc) or any((t.r, t.c) == (r, c) for t in self.troggles):
            return
        self.troggles.append(
            Troggle(r, c, self.rng.choice(TROGGLE_NAMES), min(0.25 + 0.05 * self.level, 0.7))
        )
        self._snd("troggle")

    def _end_turn(self):
        if self.over:
            return
        self.turn += 1
        if self._caught():
            return
        every = max(2, 6 - self.level // 2)
        if self.turn % every == 0:
            self._spawn_troggle()
        if self.turn % 2 == 0:  # troggles move at half the muncher's speed
            for t in self.troggles:
                self._move_troggle(t)
                if (t.r, t.c) == (self.pr, self.pc):
                    break
        self._caught()

    def _move_troggle(self, t: Troggle):
        options = [(t.r + dr, t.c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        options = [(r, c) for r, c in options if 0 <= r < ROWS and 0 <= c < COLS]
        if self.rng.random() < t.skill:
            options.sort(key=lambda p: abs(p[0] - self.pr) + abs(p[1] - self.pc))
            t.r, t.c = options[0]
        else:
            t.r, t.c = self.rng.choice(options)
        # Troggles scribble over the number they land on.
        if (t.r, t.c) != (self.pr, self.pc):
            self.grid[t.r][t.c] = self.rule.random_value(self.rng)

    def _caught(self) -> bool:
        if any((t.r, t.c) == (self.pr, self.pc) for t in self.troggles):
            who = next(t.name for t in self.troggles if (t.r, t.c) == (self.pr, self.pc))
            self.flash = "caught"
            self._snd("caught")
            self.message = f"{who.upper()} GOT YOU!" if self.lives > 1 else "GAME OVER"
            self._lose_life()
            return True
        return False

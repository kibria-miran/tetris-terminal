#!/usr/bin/env python3
"""Tetris clone for the terminal, using only the Python standard library (curses).

Run:  python3 tetris.py
"""

import curses
import random
import time

COLS = 10
ROWS = 20
CELL = 2  # cells are rendered 2 chars wide so blocks look square

EMPTY = " "

SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[1, 1, 1], [0, 1, 0]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
}

COLORS = {
    "I": curses.COLOR_CYAN,
    "O": curses.COLOR_YELLOW,
    "T": curses.COLOR_MAGENTA,
    "S": curses.COLOR_GREEN,
    "Z": curses.COLOR_RED,
    "J": curses.COLOR_BLUE,
    "L": curses.COLOR_WHITE,
}

LINE_SCORES = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}
LINES_PER_LEVEL = 10


def rotate(shape):
    """Rotate a matrix 90 degrees clockwise."""
    return [list(row) for row in zip(*shape[::-1])]


class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.shape = [row[:] for row in SHAPES[kind]]
        self.x = (COLS - len(self.shape[0])) // 2
        self.y = 0

    @staticmethod
    def cells(shape, x=0, y=0):
        for ry, row in enumerate(shape):
            for rx, filled in enumerate(row):
                if filled:
                    yield y + ry, x + rx


class Game:
    def __init__(self, rng):
        self.rng = rng
        self.board = [[EMPTY] * COLS for _ in range(ROWS)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.next_kind = self.rng.choice(list(SHAPES))
        self.hold_kind = None
        self.hold_used = False
        self.paused = False
        self.over = False
        self.piece = self.spawn()

    def spawn(self):
        piece = Piece(self.next_kind)
        self.next_kind = self.rng.choice(list(SHAPES))
        if self.collides(piece.shape, piece.x, piece.y):
            self.over = True
        return piece

    def collides(self, shape, x, y):
        for cy, cx in Piece.cells(shape, x, y):
            if cx < 0 or cx >= COLS or cy >= ROWS:
                return True
            if cy >= 0 and self.board[cy][cx] != EMPTY:
                return True
        return False

    def try_move(self, dx, dy):
        if not self.collides(self.piece.shape, self.piece.x + dx, self.piece.y + dy):
            self.piece.x += dx
            self.piece.y += dy
            return True
        return False

    def try_rotate(self):
        rotated = rotate(self.piece.shape)
        for kick in (0, -1, 1, -2, 2):
            if not self.collides(rotated, self.piece.x + kick, self.piece.y):
                self.piece.shape = rotated
                self.piece.x += kick
                return True
        return False

    def hold(self):
        if self.hold_used:
            return
        self.hold_used = True
        current = self.piece.kind
        if self.hold_kind is None:
            self.hold_kind = current
            self.piece = self.spawn()
        else:
            self.piece = Piece(self.hold_kind)
            self.hold_kind = current
            if self.collides(self.piece.shape, self.piece.x, self.piece.y):
                self.over = True

    def hard_drop(self):
        while self.try_move(0, 1):
            self.score += 2
        self.lock()

    def tick(self):
        if not self.try_move(0, 1):
            self.lock()

    def lock(self):
        for cy, cx in Piece.cells(self.piece.shape, self.piece.x, self.piece.y):
            if cy >= 0:
                self.board[cy][cx] = self.piece.kind
        self.clear_lines()
        self.piece = self.spawn()
        self.hold_used = False

    def clear_lines(self):
        kept = [row for row in self.board if any(c == EMPTY for c in row)]
        cleared = ROWS - len(kept)
        if cleared:
            self.board = [[EMPTY] * COLS for _ in range(cleared)] + kept
            self.lines += cleared
            self.score += LINE_SCORES[cleared] * self.level
            self.level = self.lines // LINES_PER_LEVEL + 1

    def fall_delay(self):
        return max(0.05, 0.8 * (0.85 ** (self.level - 1)))


def draw_cell(stdscr, y, x, kind):
    color = curses.color_pair(COLORS[kind])
    stdscr.addstr(y, x, "  " if kind else "  ", color)


def draw_preview(stdscr, top, left, kind):
    stdscr.addstr(top, left, "Next:")
    if kind is None:
        return
    shape = SHAPES[kind]
    for ry, row in enumerate(shape):
        for rx, filled in enumerate(row):
            if filled:
                draw_cell(stdscr, top + 1 + ry, left + rx * CELL, kind)


def draw_hold(stdscr, top, left, kind):
    stdscr.addstr(top, left, "Hold:")
    if kind is None:
        return
    shape = SHAPES[kind]
    for ry, row in enumerate(shape):
        for rx, filled in enumerate(row):
            if filled:
                draw_cell(stdscr, top + 1 + ry, left + rx * CELL, kind)


def draw(stdscr, game):
    stdscr.erase()
    offset_x = 0
    offset_y = 1

    stdscr.addstr(0, 0, f"Score {game.score:<6} Lines {game.lines:<4} Level {game.level}")

    for y, row in enumerate(game.board):
        for x, kind in enumerate(row):
            if kind != EMPTY:
                draw_cell(stdscr, offset_y + y, offset_x + x * CELL, kind)

    ghost_y = game.piece.y
    while not game.collides(game.piece.shape, game.piece.x, ghost_y + 1):
        ghost_y += 1
    for cy, cx in Piece.cells(game.piece.shape, game.piece.x, ghost_y):
        if cy >= 0:
            try:
                stdscr.addstr(offset_y + cy, offset_x + cx * CELL, "[]", curses.A_DIM)
            except curses.error:
                pass

    for cy, cx in Piece.cells(game.piece.shape, game.piece.x, game.piece.y):
        if cy >= 0:
            draw_cell(stdscr, offset_y + cy, offset_x + cx * CELL, game.piece.kind)

    side_x = COLS * CELL + 2
    draw_preview(stdscr, offset_y, side_x, game.next_kind)
    draw_hold(stdscr, offset_y + 6, side_x, game.hold_kind)
    stdscr.addstr(offset_y + 11, side_x, "Keys:")
    for i, line in enumerate(
        ["<-/->  move", "up/down rotate", "space  hard drop", "c      hold", "p      pause", "q      quit"]
    ):
        stdscr.addstr(offset_y + 12 + i, side_x, line)

    if game.paused and not game.over:
        stdscr.addstr(ROWS // 2 + 1, side_x, "PAUSED")
    if game.over:
        stdscr.addstr(ROWS // 2, side_x // 2, "GAME OVER - r to restart")

    stdscr.refresh()


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        for kind, color in COLORS.items():
            curses.init_pair(color, color, -1)

    game = Game(random.Random())
    last_fall = time.monotonic()

    while True:
        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            return

        if game.over:
            if key in (ord("r"), ord("R")):
                game = Game(random.Random())
                last_fall = time.monotonic()
            curses.napms(10)
            continue

        if key in (ord("p"), ord("P")):
            game.paused = not game.paused

        if not game.paused:
            if key == curses.KEY_LEFT:
                game.try_move(-1, 0)
            elif key == curses.KEY_RIGHT:
                game.try_move(1, 0)
            elif key == curses.KEY_DOWN:
                if game.try_move(0, 1):
                    game.score += 1
            elif key in (curses.KEY_UP, ord("w"), ord("W")):
                game.try_rotate()
            elif key == ord(" "):
                game.hard_drop()
            elif key in (ord("c"), ord("C")):
                game.hold()

            now = time.monotonic()
            if not game.over and now - last_fall >= game.fall_delay():
                game.tick()
                last_fall = now

        draw(stdscr, game)


def run():
    curses.wrapper(main)


if __name__ == "__main__":
    run()

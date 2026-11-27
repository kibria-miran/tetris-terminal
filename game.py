"""
Terminal Dungeon Crawler Game
A complete roguelike-style terminal game in Python.
Requires only the standard library (uses curses on Unix, msvcrt on Windows).

Run: python game.py
"""

import random
import sys
import os

# Cross-platform single-key input handling
if os.name == 'nt':
    import msvcrt

    def get_key():
        if msvcrt.kbhit():
            k = msvcrt.getch()
            if k in (b'\x00', b'\xe0'):
                k = msvcrt.getch()
                return {b'H': 'UP', b'P': 'DOWN', b'K': 'LEFT', b'M': 'RIGHT'}.get(k, None)
            k = k.decode('utf-8', errors='ignore').lower()
            return k
        return None

    def clear_screen():
        os.system('cls')
else:
    import termios
    import tty
    import select

    _stdin_fd = sys.stdin.fileno()
    try:
        _old_attrs = termios.tcgetattr(_stdin_fd)
        tty.setcbreak(_stdin_fd)
    except termios.error:
        _old_attrs = None

    def get_key():
        if select.select([sys.stdin], [], [], 0)[0]:
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                ch2 = sys.stdin.read(2)
                return {'[A': 'UP', '[B': 'DOWN', '[C': 'RIGHT', '[D': 'LEFT'}.get(ch2, None)
            return ch.lower()
        return None

    def restore_terminal():
        if _old_attrs is not None:
            termios.tcsetattr(_stdin_fd, termios.TCSADRAIN, _old_attrs)

    def clear_screen():
        os.system('clear')


# ---------------------------------------------------------------- Game Data
MAP_W, MAP_H = 40, 20
VIEW_W, VIEW_H = MAP_W, MAP_H

TILE_WALL = '#'
TILE_FLOOR = '.'
TILE_STAIRS = '>'

MONSTERS = {
    'r': {'name': 'rat',      'hp': 3,  'dmg': 1, 'xp': 5,  'char': 'r', 'color': None},
    'g': {'name': 'goblin',   'hp': 8,  'dmg': 2, 'xp': 15, 'char': 'g', 'color': None},
    'o': {'name': 'orc',      'hp': 15, 'dmg': 4, 'xp': 30, 'char': 'o', 'color': None},
}

ITEMS = {
    '!': {'name': 'Health Potion', 'type': 'heal', 'value': 10},
    '/': {'name': 'Sword',         'type': 'weapon', 'value': 2},
    '[': {'name': 'Shield',        'type': 'armor',  'value': 2},
}


class Entity:
    def __init__(self, x, y, char, hp, dmg=1, name='?'):
        self.x, self.y = x, y
        self.char = char
        self.hp = hp
        self.max_hp = hp
        self.dmg = dmg
        self.name = name


class Monster(Entity):
    def __init__(self, x, y, key):
        data = MONSTERS[key]
        super().__init__(x, y, data['char'], data['hp'], data['dmg'], data['name'])
        self.xp = data['xp']
        self.key = key


class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, '@', 20, 3, 'you')
        self.xp = 0
        self.level = 1
        self.xp_next = 20
        self.inventory = []
        self.weapon_bonus = 0
        self.armor_bonus = 0


class Game:
    def __init__(self):
        self.level_num = 1
        self.messages = []
        self.game_over = False
        self.won = False
        self.player = None
        self.map = None
        self.monsters = []
        self.items = []
        self.new_level()

    # -------------------------------------------------------- Map Generation
    def new_level(self):
        self.map = [[TILE_WALL for _ in range(MAP_W)] for _ in range(MAP_H)]
        rooms = []
        attempts = 0
        while len(rooms) < 6 and attempts < 200:
            attempts += 1
            w = random.randint(5, 9)
            h = random.randint(4, 6)
            x = random.randint(1, MAP_W - w - 1)
            y = random.randint(1, MAP_H - h - 1)
            new_room = (x, y, w, h)
            if any(self._rooms_overlap(new_room, r) for r in rooms):
                continue
            self._carve_room(*new_room)
            if rooms:
                px, py = rooms[-1][0] + rooms[-1][2] // 2, rooms[-1][1] + rooms[-1][3] // 2
                nx, ny = x + w // 2, y + h // 2
                self._carve_corridor(px, py, nx, ny)
            rooms.append(new_room)

        # Place player in first room
        rx, ry, rw, rh = rooms[0]
        px = rx + rw // 2
        py = ry + rh // 2
        self.player = Player(px, py)

        # Spawn monsters & items in other rooms
        self.monsters = []
        self.items = []
        for i, (rx, ry, rw, rh) in enumerate(rooms[1:], start=1):
            for _ in range(random.randint(1, 3)):
                mx = random.randint(rx, rx + rw - 1)
                my = random.randint(ry, ry + rh - 1)
                if (mx, my) == (px, py) or self.map[my][mx] != TILE_FLOOR:
                    continue
                tier = min(self.level_num // 3, 2)
                key = ['r', 'g', 'o'][random.randint(0, tier)]
                self.monsters.append(Monster(mx, my, key))

            if random.random() < 0.6:
                ix = random.randint(rx, rx + rw - 1)
                iy = random.randint(ry, ry + rh - 1)
                if self.map[iy][ix] == TILE_FLOOR:
                    self.items.append((ix, iy, random.choice(list(ITEMS.keys()))))

        # Stairs in last room
        rx, ry, rw, rh = rooms[-1]
        sx = rx + rw // 2
        sy = ry + rh // 2
        if self.map[sy][sx] == TILE_FLOOR:
            self.map[sy][sx] = TILE_STAIRS
        else:
            # fallback: find any floor in last room
            for yy in range(ry, ry + rh):
                for xx in range(rx, rx + rw):
                    if self.map[yy][xx] == TILE_FLOOR:
                        self.map[yy][xx] = TILE_STAIRS
                        break
                else:
                    continue
                break

        self.messages = [f"You descend to level {self.level_num}."]

    def _rooms_overlap(self, a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return not (ax + aw + 1 < bx or bx + bw + 1 < ax or
                    ay + ah + 1 < by or by + bh + 1 < ay)

    def _carve_room(self, x, y, w, h):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.map[yy][xx] = TILE_FLOOR

    def _carve_corridor(self, x1, y1, x2, y2):
        x, y = x1, y1
        while x != x2:
            self.map[y][x] = TILE_FLOOR
            x += 1 if x2 > x else -1
        while y != y2:
            self.map[y][x] = TILE_FLOOR
            y += 1 if y2 > y else -1
        self.map[y][x] = TILE_FLOOR

    # --------------------------------------------------------------- Helpers
    def msg(self, text):
        self.messages.append(text)
        if len(self.messages) > 5:
            self.messages.pop(0)

    def monster_at(self, x, y):
        for m in self.monsters:
            if m.x == x and m.y == y:
                return m
        return None

    def item_at(self, x, y):
        for it in self.items:
            if it[0] == x and it[1] == y:
                return it
        return None

    def walkable(self, x, y):
        return 0 <= x < MAP_W and 0 <= y < MAP_H and self.map[y][x] != TILE_WALL

    # ---------------------------------------------------------------- Actions
    def try_move(self, dx, dy):
        if self.game_over:
            return
        nx, ny = self.player.x + dx, self.player.y + dy
        monster = self.monster_at(nx, ny)
        if monster:
            self.attack(monster)
            return
        if not self.walkable(nx, ny):
            return
        self.player.x, self.player.y = nx, ny

        # Stairs?
        if self.map[ny][nx] == TILE_STAIRS:
            self.level_num += 1
            self.new_level()
            return

        # Item pickup
        item = self.item_at(nx, ny)
        if item:
            self.items.remove(item)
            self.pickup(item[2])

        self.monsters_turn()

    def attack(self, monster):
        dmg = self.player.dmg + self.player.weapon_bonus
        monster.hp -= dmg
        self.msg(f"You hit the {monster.name} for {dmg}.")
        if monster.hp <= 0:
            self.monsters.remove(monster)
            self.player.xp += monster.xp
            self.msg(f"The {monster.name} dies! (+{monster.xp} XP)")
            self.check_level_up()
        else:
            # monster hits back
            mdmg = max(1, monster.dmg - self.player.armor_bonus)
            self.player.hp -= mdmg
            self.msg(f"The {monster.name} hits you for {mdmg}.")
            self.check_death()

    def pickup(self, key):
        data = ITEMS[key]
        if data['type'] == 'heal':
            self.player.hp = min(self.player.max_hp, self.player.hp + data['value'])
            self.msg(f"You drink a {data['name']}. (+{data['value']} HP)")
        elif data['type'] == 'weapon':
            self.player.weapon_bonus += data['value']
            self.msg(f"You equip a {data['name']}. (+{data['value']} dmg)")
        elif data['type'] == 'armor':
            self.player.armor_bonus += data['value']
            self.msg(f"You equip a {data['name']}. (+{data['value']} armor)")

    def check_level_up(self):
        p = self.player
        while p.xp >= p.xp_next:
            p.xp -= p.xp_next
            p.level += 1
            p.xp_next = int(p.xp_next * 1.6)
            p.max_hp += 5
            p.hp = p.max_hp
            p.dmg += 1
            self.msg(f"*** Level up! You are now level {p.level}. ***")

    def check_death(self):
        if self.player.hp <= 0:
            self.player.hp = 0
            self.game_over = True
            self.msg("You have died. Game over.")

    def monsters_turn(self):
        for m in list(self.monsters):
            dx = self.player.x - m.x
            dy = self.player.y - m.y
            dist = abs(dx) + abs(dy)
            if dist == 1:
                # attack
                dmg = max(1, m.dmg - self.player.armor_bonus)
                self.player.hp -= dmg
                self.msg(f"The {m.name} hits you for {dmg}.")
                self.check_death()
            elif dist <= 6 and random.random() < 0.75:
                # chase
                move_x = 0
                move_y = 0
                if abs(dx) > abs(dy):
                    move_x = 1 if dx > 0 else -1
                else:
                    move_y = 1 if dy > 0 else -1
                nx, ny = m.x + move_x, m.y + move_y
                if self.walkable(nx, ny) and (nx, ny) != (self.player.x, self.player.y) \
                        and not any(o.x == nx and o.y == ny for o in self.monsters):
                    m.x, m.y = nx, ny

    # ---------------------------------------------------------------- Render
    def render(self):
        clear_screen()
        p = self.player
        print(f"=== DUNGEON CRAWLER — Level {self.level_num} ===")
        print(f"HP: {p.hp}/{p.max_hp}  Lvl: {p.level}  XP: {p.xp}/{p.xp_next}  "
              f"DMG: {p.dmg + p.weapon_bonus}  ARM: {p.armor_bonus}")
        print("+" + "-" * MAP_W + "+")

        # build display grid
        grid = [[' ' for _ in range(MAP_W)] for _ in range(MAP_H)]
        for y in range(MAP_H):
            for x in range(MAP_W):
                grid[y][x] = self.map[y][x]
        for (ix, iy, key) in self.items:
            grid[iy][ix] = key
        for m in self.monsters:
            grid[m.y][m.x] = m.char
        grid[p.y][p.x] = p.char

        for row in grid:
            print("|" + "".join(row) + "|")
        print("+" + "-" * MAP_W + "+")

        for m in self.messages:
            print(f"  {m}")
        if self.game_over:
            print("\n  GAME OVER. Press 'q' to quit, 'r' to restart.")
        else:
            print("\n  Move: WASD / Arrows  |  q: quit")


# ---------------------------------------------------------------- Main Loop
def main():
    game = Game()
    while True:
        game.render()
        key = get_key()
        if key is None:
            continue
        if key == 'q':
            print("\nThanks for playing!")
            break
        if game.game_over:
            if key == 'r':
                game = Game()
            continue
        if key in ('w', 'UP'):
            game.try_move(0, -1)
        elif key in ('s', 'DOWN'):
            game.try_move(0, 1)
        elif key in ('a', 'LEFT'):
            game.try_move(-1, 0)
        elif key in ('d', 'RIGHT'):
            game.try_move(1, 0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye!")
    finally:
        if os.name != 'nt':
            restore_terminal()

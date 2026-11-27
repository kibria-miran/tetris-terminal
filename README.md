# Terminal Dungeon Crawler

A complete roguelike-style terminal game in Python. Requires only the standard
library (uses `termios` on Unix, `msvcrt` on Windows).

## How to Play

**Controls:**
- `WASD` or **arrow keys** — move
- `q` — quit
- `r` — restart (after death)

**Goal:** Descend as many dungeon levels as possible. Step on `>` (stairs) to
go deeper. Enemies get tougher the deeper you go.

**Symbols:**

| Symbol | Meaning |
|--------|---------|
| `@` | You |
| `#` | Wall |
| `.` | Floor |
| `>` | Stairs (next level) |
| `r` | Rat (weak) |
| `g` | Goblin (medium) |
| `o` | Orc (strong) |
| `!` | Health Potion (+10 HP) |
| `/` | Sword (+2 damage) |
| `[` | Shield (+2 armor) |

**Mechanics:**
- **Combat:** Walk into a monster to attack; monsters also attack back.
- **XP / Leveling:** Kill monsters to earn XP. Level up = more HP, damage, and full heal.
- **Chasing:** Monsters within 6 tiles will pursue you.
- **Items:** Picked up automatically when you step on them.
- **Random dungeons:** Every level is procedurally generated with rooms and corridors.

## Install (Arch Linux)

Python is preinstalled on Arch; nothing extra is needed:

```bash
sudo pacman -S --needed python
```

Clone and play:

```bash
git clone https://github.com/kibria-miran/tetris-terminal.git
cd tetris-terminal
python game.py
```

## Notes

- **Works on Linux/macOS/Windows** — uses `termios` on Unix and `msvcrt` on Windows.
- Only **standard library** — no pip installs needed.
- The game uses `clear_screen` between frames, so it plays in any terminal.
- For best experience on Unix, run in a standard terminal (not an IDE console).
  On Windows, run in `cmd` or `PowerShell`.

## License

MIT — see [LICENSE](LICENSE).

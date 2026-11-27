# tetris-terminal

A classic Tetris clone that runs entirely in your terminal. Written in Python
using only the standard library (`curses`) — no dependencies to install.

## Features

- All 7 tetrominoes (I, O, T, S, Z, J, L) with wall-kick rotation
- Ghost piece showing where the current piece will land
- Line clears with classic scoring (100/300/500/800 × level)
- Levels that speed the game up every 10 lines
- Next-piece preview and hold slot
- Pause, game over, and instant restart

## Install (Arch Linux)

Python is preinstalled on Arch; nothing extra is needed:

```bash
sudo pacman -S --needed python
```

Clone and play:

```bash
git clone https://github.com/<you>/tetris-terminal.git
cd tetris-terminal
python3 tetris.py
```

## Controls

| Key            | Action                |
| -------------- | --------------------- |
| ← / →          | Move left / right     |
| ↑ / ↓          | Rotate / soft drop    |
| Space          | Hard drop             |
| c              | Hold piece            |
| p              | Pause                 |
| r              | Restart (after loss)  |
| q              | Quit                  |

## Scoring

| Lines cleared | Points (× level) |
| ------------- | ---------------- |
| 1             | 100              |
| 2             | 300              |
| 3             | 500              |
| 4 (Tetris)    | 800              |

Soft drop +1 per row, hard drop +2 per row.

## License

MIT — see [LICENSE](LICENSE).

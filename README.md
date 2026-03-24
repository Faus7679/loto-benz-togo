# Loto-Benz Togo — Tirage Analyzer & Number Generator

A Python system that reads historical Loto-Benz Togo draw results, analyzes frequency patterns, and suggests 5 winning numbers for each game.

## Game Rules

- Pick **5 numbers** from **1 to 90** (no repetition)
- Two daily sessions: **Midi** (~13h) and **Soir** (~19h)

## Project Structure

```
loto-benz-togo/
├── loto_benz.py        # Main script: analyzer + number generator
└── data/
    └── tirages.csv     # Historical draw database (date, session, n1–n5)
```

## Usage

```bash
# Default: show stats summary + balanced number suggestion
python3 loto_benz.py

# Suggest 5 numbers with a specific strategy
python3 loto_benz.py --suggest --strategy hot       # most frequent numbers
python3 loto_benz.py --suggest --strategy cold      # least frequent numbers
python3 loto_benz.py --suggest --strategy balanced  # mix hot + cold (default)
python3 loto_benz.py --suggest --strategy random    # pure random 1–90

# Add a new tirage to keep the system up to date
python3 loto_benz.py --add "YYYY-MM-DD,Midi|Soir,n1,n2,n3,n4,n5"
# Example:
python3 loto_benz.py --add "2026-03-25,Soir,4,19,37,61,85"

# View last N draws
python3 loto_benz.py --history 10

# Full frequency table for all 90 numbers
python3 loto_benz.py --stats
```

## Strategies

| Strategy   | Logic                                             |
| ---------- | ------------------------------------------------- |
| `hot`      | Picks from the 20 most frequently drawn numbers   |
| `cold`     | Picks from never/rarely drawn numbers             |
| `balanced` | 3 hot + 2 cold for statistical coverage (default) |
| `random`   | Pure `random.sample(1–90, 5)`                     |

## Adding New Tirages

Each time a new draw is published, add it with:

```bash
python3 loto_benz.py --add "2026-03-26,Midi,12,34,56,78,90"
```

The entry is appended to `data/tirages.csv` and immediately reflected in frequency analysis and suggestions. Duplicate entries (same date + session) are automatically rejected.

## Data Format (`data/tirages.csv`)

```
date,session,n1,n2,n3,n4,n5
2026-03-24,Midi,3,20,38,55,82
2026-03-24,Soir,9,31,41,62,79
```

> **Disclaimer:** Lotto is a game of chance. No algorithm can predict future draws. Suggestions are based on historical frequency analysis only.

#!/usr/bin/env python3
"""
Loto-Benz Togo — Tirage Analyzer & Number Generator
=====================================================
Rules:
  - 5 winning numbers drawn from 1 to 90 (no replacement)
  - Two daily sessions: Midi (~13h) and Soir (~19h)

Usage:
  python loto_benz.py                        # show stats + suggestions
  python loto_benz.py --suggest              # suggest 5 numbers only
  python loto_benz.py --strategy hot         # use "hot" numbers strategy
  python loto_benz.py --strategy cold        # use "cold" numbers strategy
  python loto_benz.py --strategy balanced    # mix hot + cold (default)
  python loto_benz.py --strategy random      # pure random (1-90)
  python loto_benz.py --add "2026-03-25,Midi,12,34,56,78,90"
  python loto_benz.py --history 10           # show last N draws
  python loto_benz.py --stats                # full frequency analysis
"""

import argparse
import csv
import os
import random
from collections import Counter
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "tirages.csv")
FIELDNAMES = ["date", "session", "n1", "n2", "n3", "n4", "n5"]
MIN_NUM, MAX_NUM, PICK = 1, 90, 5


# ─── Data helpers ────────────────────────────────────────────────────────────

def load_tirages() -> list[dict]:
    """Load all draws from the CSV file."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_tirage(row: dict) -> bool:
    """Append a single draw row to the CSV. Returns False if duplicate."""
    existing = load_tirages()
    for r in existing:
        if r["date"] == row["date"] and r["session"] == row["session"]:
            print(f"  [!] Draw already exists: {row['date']} {row['session']}")
            return False

    write_header = not os.path.exists(DATA_FILE)
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    return True


def parse_add_arg(raw: str) -> dict:
    """Parse a CSV-style string: 'YYYY-MM-DD,Session,n1,n2,n3,n4,n5'."""
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 7:
        raise ValueError(
            "Expected format: 'YYYY-MM-DD,Midi|Soir,n1,n2,n3,n4,n5'\n"
            f"  Got: {raw!r}"
        )
    date_str, session = parts[0], parts[1]
    datetime.strptime(date_str, "%Y-%m-%d")          # validate date
    if session not in ("Midi", "Soir"):
        raise ValueError(f"Session must be 'Midi' or 'Soir', got {session!r}")
    nums = [int(p) for p in parts[2:]]
    if len(nums) != PICK:
        raise ValueError(f"Need exactly {PICK} numbers")
    for n in nums:
        if not (MIN_NUM <= n <= MAX_NUM):
            raise ValueError(f"Number {n} out of range [{MIN_NUM}-{MAX_NUM}]")
    if len(set(nums)) != PICK:
        raise ValueError("Numbers must all be distinct")
    return {
        "date": date_str, "session": session,
        "n1": nums[0], "n2": nums[1], "n3": nums[2],
        "n4": nums[3], "n5": nums[4],
    }


def all_numbers(tirages: list[dict]) -> list[int]:
    """Flatten all drawn numbers from all tirages into one list."""
    nums = []
    for row in tirages:
        for key in ("n1", "n2", "n3", "n4", "n5"):
            nums.append(int(row[key]))
    return nums


# ─── Statistics ──────────────────────────────────────────────────────────────

def compute_frequency(tirages: list[dict]) -> Counter:
    return Counter(all_numbers(tirages))


def hot_numbers(freq: Counter, top: int = 15) -> list[int]:
    """Most frequently drawn numbers."""
    return [n for n, _ in freq.most_common(top)]


def cold_numbers(freq: Counter, bottom: int = 15) -> list[int]:
    """Least frequently drawn numbers (also includes never-drawn)."""
    all_possible = set(range(MIN_NUM, MAX_NUM + 1))
    drawn = set(freq.keys())
    never_drawn = list(all_possible - drawn)
    least = [n for n, _ in freq.most_common()[:-bottom - 1:-1]]
    return (never_drawn + least)[:bottom]


def due_numbers(freq: Counter, tirages: list[dict]) -> list[int]:
    """Numbers that are statistically overdue (below average frequency)."""
    if not freq:
        return list(range(MIN_NUM, MAX_NUM + 1))
    avg = sum(freq.values()) / len(range(MIN_NUM, MAX_NUM + 1))
    return [n for n in range(MIN_NUM, MAX_NUM + 1) if freq.get(n, 0) < avg]


# ─── Suggestion strategies ───────────────────────────────────────────────────

def suggest_random() -> list[int]:
    return sorted(random.sample(range(MIN_NUM, MAX_NUM + 1), PICK))


def suggest_hot(freq: Counter) -> list[int]:
    pool = hot_numbers(freq, top=20)
    if len(pool) < PICK:
        pool += [n for n in range(MIN_NUM, MAX_NUM + 1) if n not in pool]
    return sorted(random.sample(pool[:30], PICK))


def suggest_cold(freq: Counter) -> list[int]:
    pool = cold_numbers(freq, bottom=20)
    if len(pool) < PICK:
        pool += [n for n in range(MIN_NUM, MAX_NUM + 1) if n not in pool]
    return sorted(random.sample(pool[:30], PICK))


def suggest_balanced(freq: Counter) -> list[int]:
    """Mix of hot, cold and due numbers for balanced coverage."""
    hot = hot_numbers(freq, top=15)
    cold = cold_numbers(freq, bottom=15)
    # 3 from hot, 2 from cold/due for balance
    hot_pick = min(3, len(hot))
    cold_pick = PICK - hot_pick
    chosen_hot = random.sample(hot, hot_pick)
    cold_pool = [n for n in cold if n not in chosen_hot]
    if len(cold_pool) < cold_pick:
        cold_pool += [
            n for n in range(MIN_NUM, MAX_NUM + 1)
            if n not in chosen_hot and n not in cold_pool
        ]
    chosen_cold = random.sample(cold_pool[:20], cold_pick)
    return sorted(chosen_hot + chosen_cold)


def suggest(strategy: str, freq: Counter) -> list[int]:
    strategies = {
        "random": lambda: suggest_random(),
        "hot": lambda: suggest_hot(freq),
        "cold": lambda: suggest_cold(freq),
        "balanced": lambda: suggest_balanced(freq),
    }
    if strategy not in strategies:
        raise ValueError(f"Unknown strategy '{strategy}'. Choose: {', '.join(strategies)}")
    return strategies[strategy]()


# ─── Display ─────────────────────────────────────────────────────────────────

def print_banner():
    print("=" * 55)
    print("     LOTO-BENZ TOGO  |  Tirage Analyzer & Generator")
    print("     Numbers: pick 5 from 1–90  |  Range: 1–90")
    print("=" * 55)


def print_stats(tirages: list[dict], freq: Counter):
    total_draws = len(tirages)
    print(f"\n  Total tirages recorded : {total_draws}")
    if total_draws == 0:
        return
    latest = tirages[-1]
    print(f"  Latest tirage          : {latest['date']} {latest['session']} "
          f"→  {latest['n1']} {latest['n2']} {latest['n3']} {latest['n4']} {latest['n5']}")

    hot = hot_numbers(freq, top=10)
    cold = cold_numbers(freq, bottom=10)
    print(f"\n  Top-10 HOT  numbers : {hot}")
    print(f"  Top-10 COLD numbers : {cold}")


def print_history(tirages: list[dict], last_n: int):
    print(f"\n  Last {last_n} tirages:")
    print(f"  {'Date':<12} {'Session':<6}  Numbers")
    print("  " + "-" * 40)
    for row in tirages[-last_n:]:
        nums = f"{row['n1']:>2} {row['n2']:>2} {row['n3']:>2} {row['n4']:>2} {row['n5']:>2}"
        print(f"  {row['date']:<12} {row['session']:<6}  {nums}")


def print_full_stats(tirages: list[dict], freq: Counter):
    print(f"\n  Full frequency table ({len(tirages)} draws):\n")
    print(f"  {'Num':>3}  {'Freq':>4}  Bar")
    print("  " + "-" * 35)
    max_freq = max(freq.values()) if freq else 1
    for n in range(MIN_NUM, MAX_NUM + 1):
        f = freq.get(n, 0)
        bar = "█" * int(f / max_freq * 20)
        print(f"  {n:>3}  {f:>4}  {bar}")


def print_suggestion(nums: list[int], strategy: str):
    print(f"\n  ★  Suggested numbers [{strategy}]:")
    print(f"     {' — '.join(str(n) for n in nums)}")
    print()


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Loto-Benz Togo — Tirage Analyzer & Number Generator"
    )
    parser.add_argument(
        "--suggest", action="store_true",
        help="Suggest 5 numbers (use with --strategy)"
    )
    parser.add_argument(
        "--strategy", default="balanced",
        choices=["hot", "cold", "balanced", "random"],
        help="Number suggestion strategy (default: balanced)"
    )
    parser.add_argument(
        "--add", metavar="ROW",
        help="Add a new tirage: 'YYYY-MM-DD,Midi|Soir,n1,n2,n3,n4,n5'"
    )
    parser.add_argument(
        "--history", metavar="N", type=int, default=0,
        help="Show last N draws"
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Print full frequency table for all 90 numbers"
    )
    args = parser.parse_args()

    # ── Add new tirage ──
    if args.add:
        try:
            row = parse_add_arg(args.add)
        except ValueError as e:
            print(f"[ERROR] {e}")
            return
        saved = save_tirage(row)
        if saved:
            nums = f"{row['n1']} {row['n2']} {row['n3']} {row['n4']} {row['n5']}"
            print(f"  [✓] Tirage added: {row['date']} {row['session']}  →  {nums}")
        return

    tirages = load_tirages()
    freq = compute_frequency(tirages)

    print_banner()

    # ── History view ──
    if args.history:
        print_history(tirages, args.history)
        return

    # ── Full stats ──
    if args.stats:
        print_full_stats(tirages, freq)
        return

    # ── Default: stats summary + suggestion ──
    print_stats(tirages, freq)
    nums = suggest(args.strategy, freq)
    print_suggestion(nums, args.strategy)

    if args.suggest:
        # If --suggest given alone, print a few more combinations
        print("  Additional combinations:")
        for _ in range(4):
            combo = suggest(args.strategy, freq)
            print(f"     {' — '.join(str(n) for n in combo)}")
        print()


if __name__ == "__main__":
    main()

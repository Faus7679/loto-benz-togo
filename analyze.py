#!/usr/bin/env python3
"""Deep analysis of tirages to generate consistent winning numbers."""
import random
from loto_benz import load_tirages, compute_frequency, all_numbers
from collections import Counter

tirages = load_tirages()
freq = compute_frequency(tirages)

# Recent 50 tirages (recency weight)
recent = tirages[-50:]
recent_freq = compute_frequency(recent)

print("=== ANALYSIS OF", len(tirages), "TIRAGES (1407-1836) ===")
print()

print("TOP-15 HOTTEST (all time):")
for n, c in freq.most_common(15):
    print(f"  {n:>2}: {c} times")

print()
print("TOP-15 HOTTEST (last 50 draws):")
for n, c in recent_freq.most_common(15):
    print(f"  {n:>2}: {c} times")

# Numbers appearing in both hot lists = strongest
all_hot = set(n for n, _ in freq.most_common(20))
recent_hot = set(n for n, _ in recent_freq.most_common(20))
consistent = sorted(all_hot & recent_hot)
print(f"\nCONSISTENT HOT (top-20 all-time AND top-20 recent): {consistent}")

# Due numbers: not drawn in longest time
last_seen = {}
for i, row in enumerate(tirages):
    for key in ("n1", "n2", "n3", "n4", "n5"):
        last_seen[int(row[key])] = i

total = len(tirages)
overdue = sorted([(total - last_seen.get(n, 0), n) for n in range(1, 91)], reverse=True)
print("\nMOST OVERDUE (not drawn in longest time):")
for gap, n in overdue[:10]:
    print(f"  {n:>2}: last seen {gap} draws ago (freq={freq.get(n, 0)})")

# COMPOSITE SCORING: freq(35%) + recency(40%) + overdue(25%)
scores = {}
max_freq = max(freq.values()) if freq else 1
max_recent = max(recent_freq.values()) if recent_freq else 1
for n in range(1, 91):
    f_all = freq.get(n, 0) / max_freq
    f_rec = recent_freq.get(n, 0) / max_recent
    gap = total - last_seen.get(n, 0)
    overdue_score = min(gap / 50, 1.0)
    scores[n] = f_all * 0.35 + f_rec * 0.40 + overdue_score * 0.25

ranked = sorted(scores.items(), key=lambda x: -x[1])
print("\nTOP-20 BY COMPOSITE SCORE (freq + recency + overdue):")
for n, s in ranked[:20]:
    print(f"  {n:>2}: score={s:.3f}  (freq={freq.get(n, 0)}, recent={recent_freq.get(n, 0)}, last_gap={total - last_seen.get(n, 0)})")

# Pick 5 from top-15 scored — deterministic seed for consistency
top_pool = [n for n, _ in ranked[:15]]
random.seed(2026)
pick = sorted(random.sample(top_pool, 5))
print(f"\n{'='*55}")
print(f"  RECOMMENDED 5 WINNING NUMBERS:  {pick[0]} - {pick[1]} - {pick[2]} - {pick[3]} - {pick[4]}")
print(f"{'='*55}")

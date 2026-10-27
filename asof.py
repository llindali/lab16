"""FIN 43900 Lab 16: point-in-time provenance gate (standard library only)."""
from datetime import date

DECISION_DATE = "2026-03-31"  # Try "2026-04-15" for the later-date check.
# Row, ticker, month measured, date published, index.
ROWS = [
    (1, "AAA", "2026-01", "2026-02-10", 101.0),
    (2, "AAA", "2026-02", "2026-03-10", 104.0),
    (3, "AAA", "2026-03", "2026-04-10", 109.0),
    (4, "AAA", "2026-02", "2026-03-25", 103.0),
    (5, "BBB", "2026-01", "2026-02-10", 98.0),
    (6, "BBB", "2026-02", "2026-03-10", 97.0),
    (7, "BBB", "2026-02", "2026-03-10", 97.0),
    (8, "BBB", "2026-03", "2026-04-10", 92.0),
    (9, "CCC", "2026-01", "2026-02-10", 110.0),
    (10, "CCC", "2026-02", "2026-04-05", 112.0),
    (11, "", "2026-02", "2026-03-10", 99.0),
    (12, "CCC", "2026-02", "2026-03-10", 111.0),
]


def latest_vintages(rows):
    """Keep newest publication for each ticker/month (ties: first row)."""
    kept = {}
    replaced = []
    for row in rows:
        key = row[1], row[2]
        previous = kept.get(key)
        if previous is None or row[3] > previous[3]:
            if previous is not None:
                replaced.append(previous[0])
            kept[key] = row
        else:
            replaced.append(row[0])
    return sorted(kept.values(), key=lambda r: r[0]), sorted(replaced)


def panel_asof(rows, decision_date):
    # 1. Quarantine missing tickers.
    quarantine = [r[0] for r in rows if not r[1].strip()]
    valid = [r for r in rows if r[1].strip()]
    # 2. Remove exact duplicates across data fields (not row identifier).
    seen, unique, duplicate = set(), [], []
    for row in valid:
        if row[1:] in seen:
            duplicate.append(row[0])
        else:
            seen.add(row[1:])
            unique.append(row)
    # 3. Exclude observations published after the decision date.
    late = [r[0] for r in unique if r[3] > decision_date]
    known = [r for r in unique if r[3] <= decision_date]
    # 4. Retain the latest knowable vintage for each ticker/month.
    panel, revision = latest_vintages(known)
    return panel, [("Quarantined (no ticker)", quarantine),
                   ("Exact duplicates", duplicate),
                   ("Published after decision", late),
                   ("Replaced older vintages", revision)]


def signals(panel):
    by_ticker = {}
    for row in panel:
        by_ticker.setdefault(row[1], []).append(row)
    result = {}
    for ticker, observations in by_ticker.items():
        observations.sort(key=lambda r: r[2])
        if len(observations) >= 2:
            prior, last = observations[-2:]
            result[ticker] = (last[2], 100 * (last[4] / prior[4] - 1))
    return result


def main():
    date.fromisoformat(DECISION_DATE)  # Validate editable date.
    panel, funnel = panel_asof(ROWS, DECISION_DATE)
    # Naive view: no publication-date gate, but same quarantine/duplicate/revision rules.
    all_time_panel, _ = panel_asof(ROWS, "9999-12-31")
    asof, naive = signals(panel), signals(all_time_panel)
    print(f"Decision date: {DECISION_DATE}\nRow funnel:")
    for name, removed in funnel:
        print(f"  {name}: {len(removed)} removed; rows {removed}")
    print("As-of panel:")
    print("  row ticker month    published  index")
    for row_id, ticker, month, published, value in panel:
        print(f"  {row_id:>3} {ticker:>6} {month} {published} {value:>6.1f}")
    print("Signals (month of latest observation):")
    for ticker in sorted(asof):
        amonth, apct = asof[ticker]
        nmonth, npct = naive[ticker]
        print(f"  {ticker}: as-of {apct:+.2f}% ({amonth}); "
              f"naive {npct:+.2f}% ({nmonth})")


if __name__ == "__main__":
    main()

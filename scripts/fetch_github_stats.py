#!/usr/bin/env python3
"""
Fetch GitHub contribution stats for the shooter HUD.

Outputs a JSON dict to stdout:
  {
    "total_contributions": 4231,
    "days_with_contributions": 247,
    "missed_days_last_10": 3
  }

Usage:
    GITHUB_TOKEN=ghp_... GITHUB_USER=nnish16 python scripts/fetch_github_stats.py
    python scripts/fetch_github_stats.py > stats.json
"""
import json, os, sys, urllib.request, datetime


GRAPHQL_QUERY = '''
{
  user(login: "%s") {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
'''


def fetch_contributions(user: str, token: str) -> dict:
    query = json.dumps({"query": GRAPHQL_QUERY % user})
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        query.encode(),
        {"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())

    cal = (data["data"]["user"]["contributionsCollection"]["contributionCalendar"])
    total = cal["totalContributions"]

    # Flatten all days
    all_days = []
    for week in cal["weeks"]:
        for day in week["contributionDays"]:
            all_days.append(day)

    return total, all_days


def compute_stats(total: int, all_days: list) -> dict:
    today = datetime.date.today()

    # Days with at least 1 contribution (level indicator)
    days_active = sum(1 for d in all_days if d["contributionCount"] > 0)

    # Missed days in the last 10 days (heart damage)
    missed = 0
    for offset in range(1, 11):          # yesterday back 10 days
        target = (today - datetime.timedelta(days=offset)).isoformat()
        matching = [d for d in all_days if d["date"] == target]
        if not matching or matching[0]["contributionCount"] == 0:
            missed += 1

    return {
        "total_contributions": total,
        "days_with_contributions": days_active,
        "missed_days_last_10": missed,
    }


def fallback_stats() -> dict:
    """Safe defaults when GitHub API isn't available."""
    return {
        "total_contributions": 0,
        "days_with_contributions": 1,
        "missed_days_last_10": 0,
    }


if __name__ == "__main__":
    user  = os.environ.get("GITHUB_USER", "nnish16")
    token = os.environ.get("GITHUB_TOKEN", os.environ.get("METRICS_TOKEN", ""))

    if not token:
        print(json.dumps(fallback_stats()), file=sys.stdout)
        sys.exit(0)

    try:
        total, all_days = fetch_contributions(user, token)
        stats = compute_stats(total, all_days)
    except Exception as e:
        print(f"Warning: GitHub API error — {e}", file=sys.stderr)
        stats = fallback_stats()

    print(json.dumps(stats))

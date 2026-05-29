# peloton_yearly_totals.py
import os
import sys
import time
import math
import argparse
from datetime import datetime, timezone, date
from dateutil.relativedelta import relativedelta
import requests
from collections import defaultdict

API_BASE = "https://api.onepeloton.com"
USER_AGENT = "Mozilla/5.0 (compatible; PelotonTotalsScript/1.0)"

RUN_DISCIPLINE = "running"
BIKE_DISCIPLINE = "cycling"

def login_or_attach_session():
    """
    Returns: (requests.Session, user_id)
    Supports two flows:
      1) Username/password via /auth/login
      2) Existing session cookie via PELOTON_SESSION_ID
    """
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})

    session_cookie = os.environ.get("PELOTON_SESSION_ID")
    if session_cookie:
        s.cookies.set("peloton_session_id", session_cookie, domain="onepeloton.com")
        # Validate & fetch /me to obtain user_id
        me = s.get(f"{API_BASE}/api/me")
        me.raise_for_status()
        user_id = me.json().get("id")
        if not user_id:
            raise RuntimeError("Could not validate session with provided PELOTON_SESSION_ID.")
        return s, user_id

    username = os.environ.get("PELOTON_USERNAME")
    password = os.environ.get("PELOTON_PASSWORD")
    if not username or not password:
        raise RuntimeError("Set PELOTON_USERNAME and PELOTON_PASSWORD, or PELOTON_SESSION_ID.")

    resp = s.post(
        f"{API_BASE}/auth/login",
        json={"username_or_email": username, "password": password},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code == 401:
        raise RuntimeError("Login failed (401). If your account uses MFA, try setting PELOTON_SESSION_ID.")
    resp.raise_for_status()
    data = resp.json()
    user_id = data.get("user_id") or data.get("user", {}).get("id")
    if not user_id:
        # Fallback to /me
        me = s.get(f"{API_BASE}/api/me")
        me.raise_for_status()
        user_id = me.json().get("id")
    if not user_id:
        raise RuntimeError("Could not resolve user_id after login.")
    return s, user_id


def get_year_bounds(year: int):
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    return start, end


def fetch_workouts_for_year(s: requests.Session, user_id: str, start_utc: datetime, end_utc: datetime):
    """
    Generator yielding workout dicts for the given year (UTC bounds).
    Paginates via /api/user/{user_id}/workouts?limit=100&page=N
    """
    page = 0
    limit = 100
    while True:
        url = f"{API_BASE}/api/user/{user_id}/workouts?limit={limit}&page={page}"
        r = s.get(url, timeout=30)
        r.raise_for_status()
        j = r.json()
        data = j.get("data", []) or j.get("workouts", [])
        if not data:
            break

        for w in data:
            # created_at is epoch seconds (UTC)
            created_epoch = w.get("created_at")
            if created_epoch is None:
                continue
            created = datetime.fromtimestamp(created_epoch, tz=timezone.utc)
            if created < start_utc:
                # Since Peloton returns most-recent first, we can stop when we drop below start bound.
                return
            if start_utc <= created < end_utc:
                yield w

        page += 1
        # Defensive sleep to avoid hammering
        time.sleep(0.2)


def _distance_from_summary(summaries):
    """
    summaries: list of dicts, typically each with keys like 'slug', 'value', 'unit'
    Returns float distance in miles if available, else None.
    """
    if not summaries:
        return None
    # Look for distance summary
    for item in summaries:
        # Common shapes seen: {'slug': 'distance', 'value': 5.01, 'unit': 'mi'}
        slug = (item.get("slug") or item.get("name") or "").lower()
        if "distance" in slug:
            val = item.get("value")
            unit = (item.get("unit") or "").lower()
            if isinstance(val, (int, float)):
                if unit in ("mi", "mile", "miles", ""):
                    return float(val)
                if unit in ("km", "kilometer", "kilometers"):
                    # Convert to miles to keep a single internal unit; convert later for display if requested
                    return float(val) * 0.621371
    return None


def get_workout_distance_miles(s: requests.Session, workout_id: str):
    """
    Attempts to extract workout distance in miles.
    Tries /api/workout/{id}/summary first, then falls back to performance_graph.
    Returns float miles or 0.0 if unavailable.
    """
    # 1) summary endpoint
    try:
        rs = s.get(f"{API_BASE}/api/workout/{workout_id}/summary", timeout=30)
        if rs.status_code == 200:
            dist = _distance_from_summary(rs.json().get("summaries") or rs.json().get("metrics"))
            if dist is not None:
                return float(dist)
    except requests.RequestException:
        pass

    # 2) performance_graph fallback (take last value of 'distance' series)
    try:
        rp = s.get(f"{API_BASE}/api/workout/{workout_id}/performance_graph?every_n=5", timeout=30)
        if rp.status_code == 200:
            metrics = rp.json().get("metrics", [])
            for series in metrics:
                slug = (series.get("slug") or "").lower()
                if "distance" in slug and isinstance(series.get("values"), list) and series["values"]:
                    # values already in miles for runs/rides
                    last = series["values"][-1]
                    if isinstance(last, (int, float)):
                        return float(last)
    except requests.RequestException:
        pass

    return 0.0


def main():
    parser = argparse.ArgumentParser(description="Peloton yearly totals for running and cycling distance.")
    parser.add_argument("--year", type=int, default=date.today().year, help="Year to report on (default: current year)")
    parser.add_argument("--km", action="store_true", help="Also show totals in kilometers")
    args = parser.parse_args()

    s, user_id = login_or_attach_session()
    start_utc, end_utc = get_year_bounds(args.year)

    totals = {
        RUN_DISCIPLINE: 0.0,   # miles internally
        BIKE_DISCIPLINE: 0.0,
    }
    monthly = {
        RUN_DISCIPLINE: defaultdict(float),
        BIKE_DISCIPLINE: defaultdict(float),
    }

    # Iterate workouts for the year
    count_seen = 0
    for w in fetch_workouts_for_year(s, user_id, start_utc, end_utc):
        status = (w.get("status") or "").lower()
        if status and status != "complete":
            continue

        discipline = (w.get("fitness_discipline") or "").lower()
        if discipline not in (RUN_DISCIPLINE, BIKE_DISCIPLINE):
            continue

        wid = w.get("id")
        if not wid:
            continue

        distance_mi = get_workout_distance_miles(s, wid)
        totals[discipline] += distance_mi

        # Monthly bucket
        created = datetime.fromtimestamp(w["created_at"], tz=timezone.utc)
        ym = created.strftime("%Y-%m")
        monthly[discipline][ym] += distance_mi

        count_seen += 1
        # light pacing
        time.sleep(0.1)

    def fmt(mi):
        if args.km:
            km = mi / 0.621371
            return f"{mi:.2f} mi  /  {km:.2f} km"
        return f"{mi:.2f} mi"

    print(f"Peloton distance totals for {args.year}")
    print("=" * 40)
    print(f"Running: {fmt(totals[RUN_DISCIPLINE])}")
    print(f"Cycling: {fmt(totals[BIKE_DISCIPLINE])}")
    print("-" * 40)

    # Monthly breakdown tables
    # Ensure all months of the requested year are printed, even if zero
    months = []
    cur = datetime(args.year, 1, 1)
    while cur.year == args.year:
        months.append(cur.strftime("%Y-%m"))
        cur += relativedelta(months=1)

    def print_table(title, data):
        print(title)
        print("Month    Distance")
        for m in months:
            mi = data.get(m, 0.0)
            if args.km:
                km = mi / 0.621371
                print(f"{m}  {mi:8.2f} mi / {km:7.2f} km")
            else:
                print(f"{m}  {mi:8.2f} mi")
        print()

    print_table("Running (monthly)", monthly[RUN_DISCIPLINE])
    print_table("Cycling (monthly)", monthly[BIKE_DISCIPLINE])

    print(f"Workouts considered: {count_seen}")
    print("Done.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error


def load_env_file(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"").strip("'")
            os.environ.setdefault(key, value)


def request_json(url, api_key, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"ApiKey {api_key}",
            "kbn-xsrf": "true",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def main():
    env_path = os.environ.get("ENV_PATH", ".env")
    load_env_file(env_path)

    kibana_url = os.environ.get("KIBANA_URL")
    api_key = os.environ.get("API_KEY")
    kibana_space = os.environ.get("KIBANA_SPACE", "")

    if not kibana_url or not api_key:
        print("Missing required env vars: KIBANA_URL and API_KEY", file=sys.stderr)
        sys.exit(1)

    space_prefix = f"/s/{kibana_space}" if kibana_space else ""
    base_url = f"{kibana_url}{space_prefix}/api/agent_builder/agents"

    agents = [
        {
            "id": "car-broker-orchestrator",
            "name": "Car Broker Orchestrator",
            "description": "Coordinates sourcing, ranking, and client response for car shopping.",
            "labels": ["car", "broker", "orchestration"],
            "avatar_color": "#B3E5FC",
            "avatar_symbol": "CB",
            "configuration": {
                "instructions": (
                    "You are the broker orchestrator. Your job is to understand the buyer request, "
                    "translate it into a clean sourcing task, and synthesize results into a ranked shortlist. "
                    "When the sourcing agent replies with normalized listings, you must: "
                    "1) apply the buyer constraints, 2) rank by fit and value, 3) call out tradeoffs, "
                    "4) ask only 1-2 focused follow-up questions. "
                    "Always return a concise summary plus a JSON block named `shortlist` with the top 3-5 listings."
                ),
                "tools": [],
            },
        },
        {
            "id": "car-sourcing-agent",
            "name": "Car Sourcing Agent",
            "description": "Finds live car listings and normalizes results.",
            "labels": ["car", "broker", "sourcing"],
            "avatar_color": "#C8E6C9",
            "avatar_symbol": "CS",
            "configuration": {
                "instructions": (
                    "You are the sourcing agent. Use any available web tools to find live listings. "
                    "Normalize every listing into a consistent schema. If a field is missing, set it to null. "
                    "Return JSON only, with keys: query_summary, filters_applied, listings, warnings. "
                    "Listings schema: listing_id, source_name, source_url, price, currency, mileage, year, "
                    "make, model, trim, body_style, drivetrain, transmission, fuel_type, exterior_color, "
                    "interior_color, vin, location, seller_type, dealer_name, stock_number, listed_at, "
                    "fetched_at, notes, confidence."
                ),
                "tools": [],
            },
        },
    ]

    for payload in agents:
        response = request_json(base_url, api_key, payload)
        print(response)

    print("Done. Created car broker agents (or received errors if they already exist).")


if __name__ == "__main__":
    main()

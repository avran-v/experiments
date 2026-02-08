#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime


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
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def converse(base_url, api_key, agent_id, input_text, conversation_id=None):
    payload = {
        "agent_id": agent_id,
        "input": input_text,
    }
    if conversation_id:
        payload["conversation_id"] = conversation_id
    return request_json(base_url, api_key, payload)


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
    base_url = f"{kibana_url}{space_prefix}/api/agent_builder/converse"

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_path = os.path.join(output_dir, f"run_car_broker_{run_id}.json")

    buyer_prompt = (
        "Find a 2021-2023 Toyota RAV4 Hybrid under $30k within 150 miles of Chicago. "
        "Prefer under 45k miles, clean title, and one-owner."
    )

    sourcing_prompt = (
        "Sourcing request:\n"
        "- Vehicle: 2021-2023 Toyota RAV4 Hybrid\n"
        "- Price max: 30000 USD\n"
        "- Radius: 150 miles of Chicago, IL\n"
        "- Mileage: prefer <= 45000\n"
        "- Notes: clean title, one-owner if possible\n"
        "Return JSON only using the required schema."
    )

    sourcing_resp = converse(
        base_url,
        api_key,
        "car-sourcing-agent",
        input_text=sourcing_prompt,
    )

    orchestrator_prompt = (
        "Buyer request:\n"
        f"{buyer_prompt}\n\n"
        "Sourcing results (JSON):\n"
        f"{json.dumps(sourcing_resp)}\n\n"
        "Now rank and summarize for the buyer."
    )

    orchestrator_resp = converse(
        base_url,
        api_key,
        "car-broker-orchestrator",
        input_text=orchestrator_prompt,
    )

    output_payload = {
        "run_id": run_id,
        "kibana_url": kibana_url,
        "buyer_prompt": buyer_prompt,
        "sourcing_prompt": sourcing_prompt,
        "sourcing_response": sourcing_resp,
        "orchestrator_prompt": orchestrator_prompt,
        "orchestrator_response": orchestrator_resp,
    }

    with open(run_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(json.dumps(output_payload, indent=2))
    print(f"\nSaved run output to: {run_path}")


if __name__ == "__main__":
    main()

import json
import urllib.request

API_URL = "http://127.0.0.1:8001/explain"


def ask(prompt, allowed=None, default=None):
    while True:
        raw = input(f"{prompt} " + (f"[default: {default}] " if default else "")).strip().lower()
        if raw == "" and default is not None:
            return default
        if allowed is None or raw in allowed:
            return raw
        print(f"Please choose one of: {', '.join(allowed)}")


def ask_int(prompt, min_val=1, max_val=10, default=5):
    while True:
        raw = input(f"{prompt} [default: {default}] ").strip()
        if raw == "":
            return default
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(f"Enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("Please enter a whole number.")


def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("\n=== CarFit Agent (CLI) ===\n")

    fuel = ask("Fuel? (petrol/diesel/hybrid/any):", allowed={"petrol", "diesel", "hybrid", "any"}, default="any")
    body = ask("Body? (sedan/wagon/suv/hatch/any):", allowed={"sedan", "wagon", "suv", "hatch", "any"}, default="any")
    gearbox = ask("Gearbox? (auto/manual/any):", allowed={"auto", "manual", "any"}, default="any")

    reliability_priority = ask_int("Reliability priority (1-10):", default=7)
    comfort_priority = ask_int("Comfort & quietness priority (1-10):", default=5)

    prefs = {
        "fuel": None if fuel == "any" else fuel,
        "body": None if body == "any" else body,
        "gearbox": None if gearbox == "any" else gearbox,
        "reliability_priority": reliability_priority,
        "comfort_priority": comfort_priority,
    }

    print("\nSending preferences:\n", json.dumps(prefs, indent=2))

    try:
        response = post_json(API_URL, prefs)
    except Exception as e:
        print("\n❌ Could not reach the API.")
        print("Make sure the server is running:")
        print("  uvicorn app:app --host 127.0.0.1 --port 8001 --reload")
        print(f"\nError: {e}")
        return

    result = response["result"]
    explanation = response["explanation"]

    if result["total_matches"] == 0:
     print("\nNo exact matches.")
    relax = ask("Relax filters? (gearbox -> any) (y/n):", allowed={"y", "n"}, default="y")
    if relax == "y":
        prefs["gearbox"] = None
        print("\nRetrying with gearbox=any...\n", json.dumps(prefs, indent=2))
        response = post_json(API_URL, prefs)
        result = response["result"]
        explanation = response["explanation"]

    print("\n=== Top matches ===")
    for i, car in enumerate(result["top_3"], start=1):
        print(f"\n{i}) {car['name']}")
        print(f"   base_score: {car['base_score']}")
        print(f"   risk_penalty: {car['risk_penalty']}")
        print(f"   final_score: {car['final_score']}")
        if car.get("issues"):
            print("   issues:")
            for issue in car["issues"][:3]:
                print(f"     - {issue.get('issue')} (severity {issue.get('severity')}, {issue.get('recency_months')} mo)")
        if car.get("why"):
            print("   why:", "; ".join(car["why"]))

    print("\n=== Agent explanation ===")
    print(explanation)
    print("\nDone.\n")


if __name__ == "__main__":
    main()
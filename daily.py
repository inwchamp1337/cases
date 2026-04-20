import requests
import json
import time
import os
from datetime import datetime

def parse_price(price_str):
    # "$45.47" -> 45.47
    return float(price_str.replace("$", "").replace(",", ""))

def parse_steam_date(date_str):
    """Convert Steam date format 'Jan 09 2015 01: +0' to ISO format"""
    if not date_str or date_str == "N/A":
        return datetime.utcnow().isoformat()
    
    try:
        # Try ISO format first
        if "T" in date_str:
            return date_str
        
        # Try Steam format: "Jan 09 2015 01: +0"
        # Remove timezone suffix
        date_clean = date_str.split("+")[0].split("-")[0].strip()
        dt = datetime.strptime(date_clean, "%b %d %Y %H:")
        return dt.isoformat()
    except:
        # Fallback to current time
        return datetime.utcnow().isoformat()

def get_price(item):
    url = "https://steamcommunity.com/market/priceoverview/"
    
    params = {
        "appid": 730,  # Hardcoded appid for CS:GO
        "market_hash_name": item["name"],
        "currency": 1
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for attempt in range(1, 4):  # Retry up to 3 times
        try:
            print(f"  Attempt {attempt}: Fetching price for {item['name']}...")
            res = requests.get(url, params=params, headers=headers, timeout=10)
            res.raise_for_status()  # Raise HTTPError for bad responses
            data = res.json()

            if data.get("success"):
                print(f"  ✓ Retrieved price for {item['name']}")
                return {
                    "date": datetime.utcnow().isoformat(),
                    "price": parse_price(data["lowest_price"]),
                    "volume": int(data["volume"].replace(",", ""))
                }
            else:
                print(f"  ✗ API response indicates failure for {item['name']}")
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Request failed for {item['name']} - {e}")
        except ValueError as e:
            print(f"  ✗ Failed to parse response for {item['name']} - {e}")

        time.sleep(1)  # Wait before retrying

    print(f"  ✗ Failed to retrieve price after 3 attempts")
    return None


def save_price(item):
    result = get_price(item)
    if not result:
        return False

    os.makedirs("data", exist_ok=True)
    path = f"data/{item['id']}.json"

    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
        else:
            data = []

        data.append(result)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        
        return True
    except (IOError, json.JSONDecodeError) as e:
        print(f"  ✗ File error: {e}")
        return False


def update_prices():
    print("=" * 70)
    print("Starting price update process...")
    print("=" * 70)
    
    try:
        with open("cases.json", "r") as f:
            cases = json.load(f)
        print(f"✓ Loaded {len(cases)} cases from cases.json\n")
    except FileNotFoundError:
        print("✗ cases.json not found. Please ensure the file exists.")
        return
    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse cases.json - {e}")
        return

    success_cases = []
    failed_cases = []

    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] Processing: {case['name']} ({case['id']})")
        
        if save_price(case):
            success_cases.append(case['name'])
        else:
            failed_cases.append(case['name'])
        
        time.sleep(1)  # Prevent being blocked by the server

    # Summary
    print("\n" + "=" * 70)
    print(f"Price update process completed!")
    print(f"✓ Successful: {len(success_cases)}/{len(cases)}")
    print(f"✗ Failed: {len(failed_cases)}/{len(cases)}")
    
    if failed_cases:
        print(f"\nFailed cases:")
        for case in failed_cases:
            print(f"  - {case}")
    
    print("=" * 70)


if __name__ == "__main__":
    update_prices()
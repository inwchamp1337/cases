import requests
import json
import time
import os
from datetime import datetime

def parse_price(price_str):
    # "$45.47" -> 45.47
    return float(price_str.replace("$", "").replace(",", ""))

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
            print(f"Attempt {attempt}: Fetching price for {item['name']}...")
            res = requests.get(url, params=params, headers=headers, timeout=10)
            res.raise_for_status()  # Raise HTTPError for bad responses
            data = res.json()

            if data.get("success"):
                print(f"Success: Retrieved price for {item['name']}")
                return {
                    "date": datetime.utcnow().isoformat(),
                    "price": parse_price(data["lowest_price"]),
                    "volume": int(data["volume"].replace(",", ""))
                }
            else:
                print(f"Warning: API response indicates failure for {item['name']}")
        except requests.exceptions.RequestException as e:
            print(f"Error: Request failed for {item['name']} - {e}")
        except ValueError as e:
            print(f"Error: Failed to parse response for {item['name']} - {e}")

        time.sleep(2)  # Wait before retrying

    print(f"Failed: Could not retrieve price for {item['name']} after 3 attempts")
    return None


def save_price(item):
    print(f"Saving price data for {item['name']}...")
    result = get_price(item)
    if not result:
        print(f"Failed to save price for {item['name']}: No data available")
        return

    os.makedirs("data", exist_ok=True)
    path = f"data/{item['id']}.json"

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Info: No existing data file for {item['name']}, creating new one")
        data = []
    except json.JSONDecodeError as e:
        print(f"Error: Failed to read existing data for {item['name']} - {e}")
        data = []

    data.append(result)

    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Success: Saved price data for {item['name']}")
    except IOError as e:
        print(f"Error: Failed to write data for {item['name']} - {e}")


def update_prices():
    print("Starting price update process...")
    try:
        with open("cases.json", "r") as f:
            cases = json.load(f)
        print("Loaded cases.json successfully")
    except FileNotFoundError:
        print("Error: cases.json not found. Please ensure the file exists.")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse cases.json - {e}")
        return

    for case in cases:
        print(f"Processing case: {case['name']} ({case['id']})")
        save_price(case)
        time.sleep(1.5)  # Prevent being blocked by the server

    print("Price update process completed.")


if __name__ == "__main__":
    update_prices()
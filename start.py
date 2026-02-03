import requests
import time
import statistics
from tabulate import tabulate
from fake_useragent import UserAgent
import random
import urllib.parse
import sys

class VintedScraper:
    def __init__(self, region="co.uk"):
        self.base_url = f"https://www.vinted.{region}"
        self.api_url = f"https://www.vinted.{region}/api/v2/catalog/items"
        self.session = requests.Session()
        self.ua = UserAgent()
        self.headers = {
            "User-Agent": self.ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def init_session(self):
        """
        Vinted requires valid cookies (especially _vinted_fr_session) to access the API.
        We visit the homepage first to simulate a real user and get these cookies.
        """
        print(f"[*] Initializing session with {self.base_url}...")
        try:
            # First request to homepage to get cookies
            resp = self.session.get(self.base_url, headers={"User-Agent": self.ua.random})
            if resp.status_code == 200:
                print("[+] Session initialized successfully.")
                return True
            else:
                print(f"[-] Failed to initialize session. Status: {resp.status_code}")
                return False
        except Exception as e:
            print(f"[-] Error initializing session: {e}")
            return False

    def search(self, query, limit=40):
        """
        Search for items using the internal API.
        """
        if not self.session.cookies:
            if not self.init_session():
                return []

        print(f"[*] Searching for '{query}'...")
        
        # Random sleep to behave like a human
        time.sleep(random.uniform(1.5, 3.0))

        params = {
            "search_text": query,
            "page": 1,
            "per_page": limit,
            "order": "relevance" # or "newest_first", "price_low_to_high"
        }

        try:
            # Update headers with specific requirements for API
            search_headers = self.headers.copy()
            # sometimes Vinted checks referer
            search_headers["Referer"] = self.base_url 
            
            response = self.session.get(self.api_url, params=params, headers=search_headers)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                print(f"[+] Found {len(items)} items.")
                return items
            else:
                print(f"[-] Search failed. Status: {response.status_code}")
                if response.status_code in [401, 403]:
                    print("    (Bot protection might be active.)")
                return []
        except Exception as e:
            print(f"[-] Error during search: {e}")
            return []

    def analyze_deals(self, items, discount_threshold=0.85, max_hours=0):
        """
        Analyze items to find deals.
        Rule: Deal if price < (Median Price * discount_threshold)
        """
        if not items:
            return []

        parsed_items = []
        prices = []

        for item in items:
            try:
                # Handle price which is a dict: {'amount': '10.0', 'currency_code': 'GBP'}
                # or sometimes just a number
                price_data = item.get("price", {})
                
                if isinstance(price_data, dict):
                    price_val = float(price_data.get("amount", "0"))
                    currency = price_data.get("currency_code", "GBP")
                else:
                    # Fallback if it's just a number/string
                    price_val = float(price_data)
                    currency = "GBP"

                title = item.get("title", "No Title")
                # URL is often full path in 'url' field
                url = item.get("url", "")
                brand = item.get("brand_title", "")
                size_title = item.get("size_title", "").lower()
                
                # Filter out junior/kids items
                negative_keywords = ['kids', 'junior', 'jr', 'child', 'boy', 'girl', 'baby', 'toddler', 'age', 'years', 'yrs']
                title_lower = title.lower()
                
                if any(kw in title_lower for kw in negative_keywords) or any(kw in size_title for kw in negative_keywords):
                    continue

                # Timestamp extraction
                # Try photo timestamp (upload time) as proxy for listing time
                timestamp = 0
                try:
                    photos = item.get("photos", [])
                    if photos:
                        timestamp = photos[0].get("high_resolution", {}).get("timestamp", 0)
                except:
                    pass
                
                if price_val > 0:
                    parsed_items.append({
                        "title": title,
                        "brand": brand,
                        "price": price_val,
                        "currency": currency,
                        "url": url,
                        "id": item.get("id"),
                        "timestamp": timestamp
                    })
                    prices.append(price_val)
            except (ValueError, TypeError):
                continue

        if not prices:
            return []

        median_price = statistics.median(prices)
        avg_price = statistics.mean(prices)
        
        print(f"\n[Stats] Median Price: {median_price:.2f} | Average Price: {avg_price:.2f}")

        # Time filter
        current_time = time.time()
        
        deals = []
        for item in parsed_items:
            # Time check
            if max_hours > 0:
                item_age_seconds = current_time - item["timestamp"]
                item_age_hours = item_age_seconds / 3600
                if item_age_hours > max_hours:
                    continue
                item["age_hours"] = item_age_hours
            else:
                # Calculate age anyway for display
                item["age_hours"] = (current_time - item["timestamp"]) / 3600

            # Price check
            if item["price"] < (median_price * discount_threshold):
                # Calculate how much cheaper it is relative to median
                discount_pct = ((median_price - item["price"]) / median_price) * 100
                item["discount_pct"] = discount_pct
                item["link"] = item['url']
                deals.append(item)

        # Sort deals by highest discount first
        deals.sort(key=lambda x: x["discount_pct"], reverse=True)
        return deals

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Vinted Deal Finder")
    parser.add_argument("query", nargs="*", help="Search query (e.g. 'liverpool jersey')")
    parser.add_argument("--hours", type=float, default=0, help="Show items listed in the last X hours only")
    parser.add_argument("--threshold", type=float, default=0.85, help="Discount threshold (default 0.85 for 15%% off)")
    
    args = parser.parse_args()
    
    if args.query:
        query = " ".join(args.query)
    else:
        query = "liverpool jersey retro"
    
    max_hours = args.hours

    # Use co.uk as requested for Ireland proxy
    scraper = VintedScraper(region="co.uk")
    items = scraper.search(query)

    if items:
        deals = scraper.analyze_deals(items, discount_threshold=args.threshold, max_hours=max_hours) 
        
        if deals:
            print(f"\n[***] Found {len(deals)} Potential Deals (Prices < {int(args.threshold*100)}% of Median) [***]")
            if max_hours > 0:
                 print(f"[Filter] Showing items listed within the last {max_hours} hours.\n")
            else:
                 print("\n")
            
            # Prepare table
            table_data = []
            for d in deals:
                age_str = f"{d['age_hours']:.1f}h" if d['age_hours'] < 24 else f"{d['age_hours']/24:.1f}d"
                table_data.append([
                    d['title'][:30], 
                    d['brand'][:15],
                    f"{d['price']} {d['currency']}",
                    f"{d['discount_pct']:.0f}%",
                    age_str,
                    d['link']
                ])
            
            print(tabulate(table_data, headers=["Title", "Brand", "Price", "-%", "Age", "Link"], tablefmt="grid"))
        else:
            print("\nNo deals found matching criteria.")
            if max_hours > 0:
                print(f"Try increasing the time range (current: {max_hours} hours).")
            
    else:
        print("No items found.")

if __name__ == "__main__":
    main()

from flask import Flask, request, jsonify
import requests
import time
import statistics
from fake_useragent import UserAgent
import random

app = Flask(__name__)

# --- Scraper Logic (Ported from start.py) ---

class VintedScraper:
    def __init__(self, region="co.uk"):
        self.base_url = f"https://www.vinted.{region}"
        self.api_url = f"https://www.vinted.{region}/api/v2/catalog/items"
        self.session = requests.Session()
        self.ua = UserAgent()
        # Vercel IP might be flagged, so we need robust headers
        self.headers = {
            "User-Agent": self.ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def init_session(self):
        try:
            resp = self.session.get(self.base_url, headers={"User-Agent": self.ua.random}, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def search(self, query, limit=40):
        if not self.session.cookies:
            self.init_session()

        time.sleep(1) # Small delay to be polite

        params = {
            "search_text": query,
            "page": 1,
            "per_page": limit,
            "order": "relevance"
        }

        try:
            search_headers = self.headers.copy()
            search_headers["Referer"] = self.base_url 
            
            response = self.session.get(self.api_url, params=params, headers=search_headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                return items
            return []
        except Exception:
            return []

    def analyze_deals(self, items, discount_threshold=0.85, max_hours=0, size_filter=None):
        if not items:
            return []

        parsed_items = []
        prices = []

        for item in items:
            try:
                price_data = item.get("price", {})
                if isinstance(price_data, dict):
                    price_val = float(price_data.get("amount", "0"))
                    currency = price_data.get("currency_code", "GBP")
                else:
                    price_val = float(price_data)
                    currency = "GBP"

                title = item.get("title", "No Title")
                url = item.get("url", "")
                brand = item.get("brand_title", "")
                size_title = item.get("size_title", "")
                
                # Filter out junior/kids items
                negative_keywords = ['kids', 'junior', 'jr', 'child', 'boy', 'girl', 'baby', 'toddler', 'age', 'years', 'yrs']
                title_lower = title.lower()
                size_lower = size_title.lower()
                
                if any(kw in title_lower for kw in negative_keywords) or any(kw in size_lower for kw in negative_keywords):
                    continue

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
                        "size": size_title,
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
        current_time = time.time()
        
        deals = []
        for item in parsed_items:
            # Time check
            item_age_hours = 0
            if item["timestamp"] > 0:
                 item_age_hours = (current_time - item["timestamp"]) / 3600
            
            item["age_hours"] = item_age_hours

            if max_hours > 0 and item_age_hours > max_hours:
                continue

            # Size filter check
            if size_filter and size_filter.strip() and size_filter.lower() not in item['size'].lower():
                continue

            # Price check
            if item["price"] < (median_price * discount_threshold):
                discount_pct = ((median_price - item["price"]) / median_price) * 100
                item["discount_pct"] = discount_pct
                item["link"] = item['url']
                deals.append(item)

        deals.sort(key=lambda x: x["discount_pct"], reverse=True)
        return deals

# --- API Route ---

# Vercel Serverless handles the routing to this file.
# Depending on configuration, it might strip the prefix or pass it through.
# We'll listen on multiple paths to be safe.

@app.route('/api/search')
@app.route('/search')
def search_endpoint():
    return search_handler()

def search_handler():
    query = request.args.get('q', 'liverpool jersey')
    hours = float(request.args.get('hours', 0))
    threshold = float(request.args.get('threshold', 0.85))
    size = request.args.get('size', None)

    scraper = VintedScraper(region="co.uk")
    items = scraper.search(query)
    
    if items:
        deals = scraper.analyze_deals(items, discount_threshold=threshold, max_hours=hours, size_filter=size)
        return jsonify(deals)
    
    return jsonify([])

# For local testing
if __name__ == '__main__':
    app.run(debug=True, port=8000)

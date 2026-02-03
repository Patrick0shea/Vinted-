# 🇮🇪 Vinted Deal Finder - Ireland 

A high-performance automated deal finder for **Vinted.ie**. This application scans live listings, calculates the median market price for any query, and highlights items listed at 15% (or more) below that price.

Live Demo: [vinted-patrick.vercel.app](https://vinted-patrick.vercel.app)

## 🚀 Features

- **Live Market Analysis**: Calculates the real-time median price for any search query.
- **Dynamic Filtering**:
  - **Time**: Find items listed in the last 5, 12, or 24 hours.
  - **Deal Strength**: Filter by discount percentage (10% to 50% off market average).
  - **Size**: Target specific sizes (M, L, XL, etc.) to skip irrelevant listings.
- **Automated Anti-Spam**: Automatically filters out "junior", "kids", and "baby" items from adult searches.
- **Vercel Enabled**: Built to run on Vercel Serverless Functions for 24/7 availability with zero server costs.

## 🛠 Tech Stack

- **Backend**: Python 3.9 (Flask)
- **Scraping**: `requests`, `fake-useragent`
- **Hosting**: Vercel (Serverless Functions)
- **Frontend**: Vanilla HTML5 / CSS3 (Glassmorphism design)
- **Deployment**: GitHub Actions / Vercel Integration

## 📂 Project Structure

```bash
├── api/
│   ├── index.py          # Flask API & Scraper Logic
│   └── requirements.txt  # Python Dependencies
├── index.html            # Premium UI Dashboard
├── vercel.json           # API Routing Configuration
└── start.py              # CLI Version (for local testing)
```

## ⚙️ How It Works

1. **Request**: The frontend sends a search query + filters to the `/api/search` endpoint.
2. **Scrape**: The Python backend initializes a secure session with Vinted.ie and fetches the latest results.
3. **Analyze**: 
   - It collects all prices from the search results.
   - It calculates the **Median Price** (Market Average).
   - It filters out items that are too old or don't match the user's size.
4. **Identify**: Any item listed significantly below the median is flagged as a "Deal".
5. **Display**: Results are returned as JSON and rendered into beautiful, interactive cards.

## 💻 Local Development

1. **Clone the Repo**:
   ```bash
   git clone https://github.com/Patrick0shea/Vinted-.git
   cd Vinted-
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r api/requirements.txt
   ```

3. **Run Localy**:
   ```bash
   python api/index.py
   ```
   The API will be available at `http://localhost:8000/api/search?q=stone island`

## 📝 License

MIT License - feel free to use and modify!

---
*Created for the Irish resale market.*

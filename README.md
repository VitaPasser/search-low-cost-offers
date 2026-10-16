# Search Low-Cost Offers

An automated scraper and aggregator for budget real estate rental offers from popular platforms:
* **Bucharest (Romania):** [olx.ro](https://www.olx.ro), [imobiliare.ro](https://www.imobiliare.ro) (budget €400–€450)
* **Łódź (Poland):** [otodom.pl](https://www.otodom.pl) (budget €400)

---

## 🕒 Scraping Schedule

| Source         | Launch Time (Daily) |
|:---------------|:--------------------|
| **otodom**     | 18:30               |
| **imobiliare** | 18:40               |
| **olx**        | 18:50               |

---

## 🌐 Web Interface

Once running, the web UI is available at:  
👉 [http://localhost:8080](http://localhost:8080)

---

## ⚙️ Installation & Setup

Prerequisites: **Docker** and the **[uv](https://docs.astral.sh/uv/getting-started/installation/)** package manager.

### 1. Initialize Sessions
Before running the app via Docker, you need to generate active session tokens for the target websites.

Install dependencies locally:
```bash
uv sync
```

Make a new .env `cp example.env .env` and fill in all the blanks.

Run the corresponding script for the platforms you wish to scrape:

* **OLX (Romania):**
```bash
uv run python -m src.scraping_lib.download_html_home_offers.olx
```

* **Otodom (Poland):**
```bash
uv run python -m src.scraping_lib.download_html_home_offers.otodom
```

* **Imobiliare (Romania):**
```bash
uv run python -m src.scraping_lib.download_html_home_offers.imobiliare
```

### 2. Run with Docker

After sessions are created, start the application containers:

```bash
docker compose up -d
```

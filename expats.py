import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json
import re
import os
import csv


LISTING_URLS = {
    "forSale": "https://www.expatriates.com/classifieds/riyadh/for-sale/",
    "vehicles-cars-trucks": "https://www.expatriates.com/classifieds/riyadh/vehicles-cars-trucks/",
    "details": "https://www.expatriates.com/cls/61729054.html"
}

CHECK_INTERVAL = 1 * 60 
DATA_FILE = "seen_listings.json"
CSV_FILE = "listings.csv"

def load_seen_listings():
    """Load seen listings from a JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_seen_listings(seen):
    """Save seen listings to disk."""
    with open(DATA_FILE, "w") as f:
        json.dump(seen, f, indent=2)


def get_html(url):
    """Fetch HTML with a user-agent header."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ListingChecker/1.0; +https://example.com)"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


# def parse_listings(html, category):
#     """Extract listings from expatriates.com HTML using BeautifulSoup."""
#     soup = BeautifulSoup(html, "lxml")
#     listings = []

#     for li in soup.select("[epoch]"):  
#         try:
#             epoch = li.get("epoch")
#             premium = li.get("premium") == "True"
#             a_tag = li.select_one("a[href*='/cls/']")
#             if not a_tag:
#                 continue

#             title_text = a_tag.text.strip()
#             href = a_tag["href"]
#             link = f"https://www.expatriates.com{href}"

#             img_tag = li.select_one("img")
#             if img_tag and img_tag.get("src"):
#                 img_url = img_tag["src"]
               
#                 if img_url.startswith("/"):
#                     img_url = f"https://www.expatriates.com{img_url}"
#             else:
#                 img_url = "No image"

#             price = "Price not specified"
#             title = title_text
#             price_match = re.match(r"^(SAR\s*[\d,]+(?:\.\d+)?|SR\s*[\d,]+(?:\.\d+)?),\s*(.*)", title_text, re.I)
#             if price_match:
#                 price = price_match.group(1)
#                 title = price_match.group(2)

            
#             user_content = li.select_one(".user-content")
#             description = user_content.text.strip() if user_content else "No description available"

           
#             posted_date = datetime.fromtimestamp(int(epoch)).strftime("%Y-%m-%d %H:%M:%S")

#             listing_id = f"{category}_{epoch}_{hash(title)}"
#             # phone_link = a_tag.text.strip()

#             listings.append({
#                 "id": listing_id,
#                 "category": category,
#                 "title": title,
#                 "price": price,
#                 "description": description,
#                 "link": link,
#                 "image": img_url,
#                 "premium": premium,
#                 "posted_date": posted_date,
#                 # "phone-link": phone_link
#             })
#         except Exception as e:
#             print(f"Error parsing listing: {e}")
#             continue

#     return listings

def parse_listings(html, category):
    """Extract listings from expatriates.com HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, "lxml")
    listings = []

    for li in soup.select("li[epoch]"):
        try:
            epoch = li.get("epoch")
            premium = li.get("premium") == "True"

            # Extract main link and title
            a_tag = li.select_one("a[href*='/cls/']:not(:has(img))")  # skip image link
            if not a_tag:
                continue

            title_text = " ".join(a_tag.text.strip().split())
            href = a_tag["href"]
            link = f"https://www.expatriates.com{href}"

            # Extract image
            img_tag = li.select_one("img")
            img_url = "No image"
            if img_tag and img_tag.get("src"):
                img_url = img_tag["src"]
                if img_url.startswith("/"):
                    img_url = f"https://www.expatriates.com{img_url}"

            # Extract price and clean title
            price = "Price not specified"
            title = title_text
            price_match = re.match(r"^(SAR|SR)\s*([\d,]+(?:\.\d+)?),\s*(.*)", title_text, re.I)
            if price_match:
                price = f"{price_match.group(1).upper()} {price_match.group(2)}"
                title = price_match.group(3)

            # Extract optional location text
            location = None
            location_text = li.get_text(" ", strip=True)
            loc_match = re.search(r"\b(RIYADH|JEDDAH|DAMMAM|SAUDI ARABIA)\b.*", location_text, re.I)
            if loc_match:
                location = loc_match.group(0)

            # Extract readable date if present
            date_div = li.select_one(".epoch")
            posted_readable = date_div.text.strip() if date_div else None

            # Fallback: epoch timestamp
            posted_date = datetime.fromtimestamp(int(epoch)).strftime("%Y-%m-%d %H:%M:%S")

            listing_id = f"{category}_{epoch}_{hash(title)}"

            listings.append({
                "id": listing_id,
                "category": category,
                "title": title,
                "price": price,
                "description": title,  # Using title text as description fallback
                "link": link,
                "image": img_url,
                "premium": premium,
                "location": location or "Unknown",
                "posted_date": posted_readable or posted_date,
            })
        except Exception as e:
            print(f"Error parsing listing: {e}")
            continue

    return listings


# def save_to_csv(listings, filename=CSV_FILE):
#     """Append new listings to a CSV file, creating it if it doesn't exist."""
#     file_exists = os.path.exists(filename)

#     with open(filename, "a", newline="", encoding="utf-8") as csvfile:
#         fieldnames = ["id", "category", "title", "price", "description", "link", "image", "premium", "posted_date"]
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

#         if not file_exists:
#             writer.writeheader()

#         for listing in listings:
#             writer.writerow(listing)

def save_to_csv(listings, filename=CSV_FILE):
    """Append new listings to a CSV file, creating it if it doesn't exist."""
    file_exists = os.path.exists(filename)

    with open(filename, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "id", "category", "title", "price", "description",
            "link", "image", "premium", "location", "posted_date"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for listing in listings:
            writer.writerow(listing)


def check_new_listings():
    seen_listings = load_seen_listings()
    new_found = []

    for category, url in LISTING_URLS.items():
        print(f"\n🔍 Checking category: {category}")
        try:
            html = get_html(url)
            parsed = parse_listings(html, category)
            print(f"Found {len(parsed)} listings on page")

            for listing in parsed:
                if listing["id"] not in seen_listings:
                    seen_listings[listing["id"]] = True
                    new_found.append(listing)
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    if new_found:
        print(f"\n🚨 {len(new_found)} new listings found!\n")
        for listing in new_found[:5]:
            print(f"[{listing['category']}] {listing['title']} - {listing['price']}")
            print(f"{listing['link']}")
            print(f"Image: {listing['image']}")
            print(f"Posted: {listing['posted_date']}")
            print("-" * 50)

        save_to_csv(new_found)
        print(f"✅ Saved {len(new_found)} new listings to CSV ({os.path.abspath(CSV_FILE)}).\n")
    else:
        print("No new listings found.")

    save_seen_listings(seen_listings)


if __name__ == "__main__":
    print("🚀 Expatriates.com Listing Scraper (with Images & CSV)")
    print(f"Saving CSV to: {os.path.abspath(CSV_FILE)}\n")

    while True:
        check_new_listings()
        print(f"Sleeping for {CHECK_INTERVAL/60:.0f} minutes...\n")
        time.sleep(CHECK_INTERVAL)

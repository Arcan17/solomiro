#!/usr/bin/env python3
"""
Scrape real car spec data from Chilean brand websites and update cars.json
"""

import json
import re
import time

from scrapling.fetchers import StealthyFetcher

fetcher = StealthyFetcher()


def fetch_page(url, use_network_idle=True, timeout=30000):
    try:
        if use_network_idle:
            page = fetcher.fetch(url, headless=True, network_idle=True, timeout=timeout)
        else:
            page = fetcher.fetch(url, headless=True, timeout=timeout)
        return page
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def get_text(page):
    if page is None:
        return ""
    try:
        return page.get_all_text()
    except Exception:
        return ""


def parse_clp_price(text):
    """Extract the first price in CLP format like $XX.XXX.XXX"""
    # Look for Chilean peso prices
    patterns = [
        r"\$\s*([\d]{1,3}(?:\.[\d]{3})+)",  # $XX.XXX.XXX
        r"(\d{2,3}[\.,]\d{3}[\.,]\d{3})\s*(?:pesos|CLP)",
    ]
    for pat in patterns:
        matches = re.findall(pat, text)
        for m in matches:
            cleaned = m.replace(".", "").replace(",", "")
            val = int(cleaned)
            if 5_000_000 <= val <= 200_000_000:  # sanity check
                return val
    return None


def parse_kpl(text):
    """Extract km/L consumption value - prefer Mixto/Combinado"""
    # Toyota format: (Km/Lt): 25,6 Ciudad - 23,3 Mixto - 21,7 Carretera
    toyota_match = re.search(
        r"Km/Lt\)?\s*:?\s*([\d,\.]+)\s*Ciudad\s*[-–]\s*([\d,\.]+)\s*Mixto\s*[-–]\s*([\d,\.]+)\s*Carretera",
        text,
        re.IGNORECASE,
    )
    if toyota_match:
        mixto = toyota_match.group(2).replace(",", ".")
        return round(float(mixto), 1)

    # Single mixto/combinado value
    for pattern in [
        r"[Mm]ixto[^:]*:?\s*([\d,\.]+)\s*[Kk]m",
        r"[Cc]ombinado[^:]*:?\s*([\d,\.]+)\s*[Kk]m",
        r"[Cc]onsumoo?\s+[Mm]ixto[^:]*:?\s*([\d,\.]+)",
        r"rendimiento[^:]*:?\s*([\d,\.]+)\s*km/[lL]",
        r"consumo[^:]*:?\s*([\d,\.]+)\s*km/[lL]",
        r"([\d,\.]+)\s*[Kk]m/[Ll]t?\b",
        r"[Ee]ficiencia.*?([\d,\.]+)\s*[Kk]m/[Ll]",
    ]:
        m = re.search(pattern, text)
        if m:
            val_str = m.group(1).replace(",", ".")
            try:
                val = float(val_str)
                if 5.0 <= val <= 35.0:
                    return round(val, 1)
            except Exception:
                pass

    # L/100km format -> convert
    for pattern in [
        r"([\d,\.]+)\s*[Ll]/100\s*[Kk]m",
        r"consumo[^:]*:?\s*([\d,\.]+)\s*[Ll]/100",
    ]:
        m = re.search(pattern, text)
        if m:
            val_str = m.group(1).replace(",", ".")
            try:
                lper100 = float(val_str)
                if 3.0 <= lper100 <= 20.0:
                    return round(100.0 / lper100, 1)
            except Exception:
                pass

    return None


def parse_power_hp(text):
    """Extract HP/CV value"""
    for pattern in [
        r"(\d{2,4})\s*[Hh][Pp]",
        r"(\d{2,4})\s*[Cc][Vv]\b",
        r"(\d{2,4})\s*[Cc]aballos",
        r"[Pp]otencia[^:]*:?\s*([\d]+)",
    ]:
        m = re.search(pattern, text)
        if m:
            val = int(m.group(1))
            if 50 <= val <= 700:
                return val
    return None


def parse_kwh100km(text):
    """Extract kWh/100km for electric vehicles"""
    for pattern in [
        r"([\d,\.]+)\s*[Kk][Ww][Hh]/100\s*[Kk]m",
        r"[Cc]onsumo[^:]*:?\s*([\d,\.]+)\s*[Kk][Ww][Hh]",
        r"([\d,\.]+)\s*[Kk][Ww][Hh]\s*/\s*100",
    ]:
        m = re.search(pattern, text)
        if m:
            val_str = m.group(1).replace(",", ".")
            try:
                val = float(val_str)
                if 8.0 <= val <= 35.0:
                    return round(val, 1)
            except Exception:
                pass
    return None


def parse_range_km(text):
    """Extract electric range"""
    for pattern in [
        r"autonomía[^:]*:?\s*([\d,\.]+)\s*[Kk]m",
        r"[Rr]ange[^:]*:?\s*([\d,\.]+)\s*[Kk]m",
        r"([\d]{3,4})\s*[Kk]m\s+(?:de\s+)?(?:autonomía|range)",
    ]:
        m = re.search(pattern, text)
        if m:
            val_str = m.group(1).replace(",", "").replace(".", "")
            try:
                val = int(val_str)
                if 100 <= val <= 1000:
                    return val
            except Exception:
                pass
    return None


# =====================================================================
# SCRAPERS PER BRAND
# =====================================================================

scraped = {}  # key: car identifier -> dict with extracted data


def scrape_toyota():
    print("\n=== Scraping Toyota Chile ===")
    urls = [
        (
            "Toyota Corolla Cross Hybrid",
            "https://toyota.cl/modelos/suv/corolla-cross-hybrid/",
        ),
        ("Toyota Corolla Cross 2.0", "https://toyota.cl/modelos/suv/corolla-cross/"),
        ("Toyota Corolla Sedan", "https://toyota.cl/modelos/sedan/corolla-sedan/"),
        ("Toyota Yaris Sedan", "https://toyota.cl/modelos/sedan/new-yaris-sedan/"),
        (
            "Toyota Yaris Sedan Hybrid",
            "https://toyota.cl/modelos/sedan/new-yaris-sedan-hybrid/",
        ),
        ("Toyota RAV4 Hybrid", "https://toyota.cl/modelos/suv/all-new-rav4-hibrido/"),
        ("Toyota RAV4 2.5", "https://toyota.cl/modelos/suv/all-new-rav4/"),
        ("Toyota Raize", "https://toyota.cl/modelos/suv/Raize/"),
        ("Toyota Fortuner", "https://toyota.cl/modelos/suv/fortuner/"),
        ("Toyota Hilux", "https://toyota.cl/modelos/pickup/hilux/"),
        (
            "Toyota Yaris Cross Hybrid",
            "https://toyota.cl/modelos/suv/yaris-cross-hybrid/",
        ),
        ("Toyota bZ4X", "https://toyota.cl/modelos/suv/auto-electrico-toyota-bz4x/"),
    ]
    for name, url in urls:
        print(f"  Fetching {name}...")
        page = fetch_page(url, use_network_idle=True, timeout=35000)
        if page is None:
            page = fetch_page(url, use_network_idle=False, timeout=25000)
        text = get_text(page)
        if not text:
            print("    -> No text")
            continue
        kpl = parse_kpl(text)
        price = parse_clp_price(text)
        hp = parse_power_hp(text)
        kwh = parse_kwh100km(text)
        rng = parse_range_km(text)
        print(f"    -> kpl={kpl}, price={price}, hp={hp}, kwh={kwh}, range={rng}")
        scraped[name] = {
            "kpl": kpl,
            "price": price,
            "hp": hp,
            "kwh": kwh,
            "range": rng,
            "url": url,
        }
        time.sleep(1)


def scrape_mazda():
    print("\n=== Scraping Mazda Chile ===")
    urls = [
        ("Mazda CX-5", "https://www.mazda.cl/vehiculo/mazda-cx-5/"),
        ("Mazda CX-30", "https://www.mazda.cl/vehiculo/mazda-cx-30/"),
        ("Mazda CX-3", "https://www.mazda.cl/vehiculo/mazda-cx-3/"),
        ("Mazda CX-60", "https://www.mazda.cl/vehiculo/mazda-cx-60/"),
        ("Mazda CX-90", "https://www.mazda.cl/vehiculo/mazda-cx-90/"),
        ("Mazda 3 Sedan", "https://www.mazda.cl/vehiculo/mazda3-sedan/"),
        ("Mazda 3 Sport", "https://www.mazda.cl/vehiculo/mazda3-sport/"),
        ("Mazda BT-50", "https://www.mazda.cl/vehiculo/bt-50/"),
    ]
    for name, url in urls:
        print(f"  Fetching {name}...")
        page = fetch_page(url, use_network_idle=True, timeout=35000)
        if page is None:
            page = fetch_page(url, use_network_idle=False, timeout=25000)
        text = get_text(page)
        if not text:
            print("    -> No text")
            continue
        kpl = parse_kpl(text)
        price = parse_clp_price(text)
        hp = parse_power_hp(text)
        print(f"    -> kpl={kpl}, price={price}, hp={hp}")
        scraped[name] = {
            "kpl": kpl,
            "price": price,
            "hp": hp,
            "kwh": None,
            "range": None,
            "url": url,
        }
        time.sleep(1)


def scrape_hyundai():
    print("\n=== Scraping Hyundai Chile ===")
    urls = [
        ("Hyundai Tucson", "https://www.hyundai.com/cl/es/vehicles/tucson"),
        ("Hyundai Santa Fe", "https://www.hyundai.com/cl/es/vehicles/santa-fe"),
        ("Hyundai Elantra", "https://www.hyundai.com/cl/es/vehicles/elantra"),
        ("Hyundai Accent", "https://www.hyundai.com/cl/es/vehicles/accent"),
        ("Hyundai Ioniq 5", "https://www.hyundai.com/cl/es/vehicles/ioniq5"),
        ("Hyundai Ioniq 6", "https://www.hyundai.com/cl/es/vehicles/ioniq6"),
        ("Hyundai Creta", "https://www.hyundai.com/cl/es/vehicles/creta"),
    ]
    for name, url in urls:
        print(f"  Fetching {name}...")
        page = fetch_page(url, use_network_idle=True, timeout=35000)
        if page is None:
            page = fetch_page(url, use_network_idle=False, timeout=25000)
        text = get_text(page)
        if not text:
            print("    -> No text")
            continue
        kpl = parse_kpl(text)
        price = parse_clp_price(text)
        hp = parse_power_hp(text)
        kwh = parse_kwh100km(text)
        rng = parse_range_km(text)
        print(f"    -> kpl={kpl}, price={price}, hp={hp}, kwh={kwh}, range={rng}")
        scraped[name] = {
            "kpl": kpl,
            "price": price,
            "hp": hp,
            "kwh": kwh,
            "range": rng,
            "url": url,
        }
        time.sleep(1)


def scrape_kia():
    print("\n=== Scraping Kia Chile ===")
    urls = [
        ("Kia Sportage", "https://www.kia.cl/modelos/sportage/"),
        ("Kia Sorento", "https://www.kia.cl/modelos/sorento/"),
        ("Kia Seltos", "https://www.kia.cl/modelos/seltos/"),
        ("Kia Cerato", "https://www.kia.cl/modelos/cerato/"),
        ("Kia Stinger", "https://www.kia.cl/modelos/stinger/"),
        ("Kia EV6", "https://www.kia.cl/modelos/ev6/"),
        ("Kia Picanto", "https://www.kia.cl/modelos/picanto/"),
    ]
    for name, url in urls:
        print(f"  Fetching {name}...")
        page = fetch_page(url, use_network_idle=True, timeout=35000)
        if page is None:
            page = fetch_page(url, use_network_idle=False, timeout=25000)
        text = get_text(page)
        if not text:
            print("    -> No text")
            continue
        kpl = parse_kpl(text)
        price = parse_clp_price(text)
        hp = parse_power_hp(text)
        kwh = parse_kwh100km(text)
        rng = parse_range_km(text)
        print(f"    -> kpl={kpl}, price={price}, hp={hp}, kwh={kwh}, range={rng}")
        scraped[name] = {
            "kpl": kpl,
            "price": price,
            "hp": hp,
            "kwh": kwh,
            "range": rng,
            "url": url,
        }
        time.sleep(1)


def scrape_chevrolet():
    print("\n=== Scraping Chevrolet Chile ===")
    urls = [
        ("Chevrolet Tracker", "https://www.chevrolet.cl/autos/tracker"),
        ("Chevrolet Captiva", "https://www.chevrolet.cl/autos/captiva"),
        ("Chevrolet Sail", "https://www.chevrolet.cl/autos/sail"),
        ("Chevrolet Onix", "https://www.chevrolet.cl/autos/onix"),
        ("Chevrolet Montana", "https://www.chevrolet.cl/autos/montana"),
    ]
    for name, url in urls:
        print(f"  Fetching {name}...")
        page = fetch_page(url, use_network_idle=True, timeout=35000)
        if page is None:
            page = fetch_page(url, use_network_idle=False, timeout=25000)
        text = get_text(page)
        if not text:
            print("    -> No text")
            continue
        kpl = parse_kpl(text)
        price = parse_clp_price(text)
        hp = parse_power_hp(text)
        print(f"    -> kpl={kpl}, price={price}, hp={hp}")
        scraped[name] = {
            "kpl": kpl,
            "price": price,
            "hp": hp,
            "kwh": None,
            "range": None,
            "url": url,
        }
        time.sleep(1)


def scrape_mg():
    print("\n=== Scraping MG Chile ===")
    urls = [
        ("MG ZS", "https://www.mg.cl/modelos/zs/"),
        ("MG ZS EV", "https://www.mg.cl/modelos/zs-ev/"),
        ("MG HS", "https://www.mg.cl/modelos/hs/"),
        ("MG MG4", "https://www.mg.cl/modelos/mg4/"),
        ("MG One PHEV", "https://www.mg.cl/modelos/one/"),
        ("MG Marvel R", "https://www.mg.cl/modelos/marvel-r/"),
    ]
    for name, url in urls:
        print(f"  Fetching {name}...")
        page = fetch_page(url, use_network_idle=True, timeout=35000)
        if page is None:
            page = fetch_page(url, use_network_idle=False, timeout=25000)
        text = get_text(page)
        if not text:
            print("    -> No text")
            continue
        kpl = parse_kpl(text)
        price = parse_clp_price(text)
        hp = parse_power_hp(text)
        kwh = parse_kwh100km(text)
        rng = parse_range_km(text)
        print(f"    -> kpl={kpl}, price={price}, hp={hp}, kwh={kwh}, range={rng}")
        scraped[name] = {
            "kpl": kpl,
            "price": price,
            "hp": hp,
            "kwh": kwh,
            "range": rng,
            "url": url,
        }
        time.sleep(1)


def scrape_byd():
    print("\n=== Scraping BYD Chile ===")
    urls = [
        ("BYD Atto 3", "https://www.byd.com/cl/auto/byd-atto3.html"),
        ("BYD Dolphin", "https://www.byd.com/cl/auto/byd-dolphin.html"),
        ("BYD Han EV", "https://www.byd.com/cl/auto/byd-han.html"),
        ("BYD Seal DM-i", "https://www.byd.com/cl/auto/byd-seal.html"),
        ("BYD Song Pro", "https://www.byd.com/cl/auto/byd-song-pro.html"),
        ("BYD Tang EV", "https://www.byd.com/cl/auto/byd-tang.html"),
    ]
    for name, url in urls:
        print(f"  Fetching {name}...")
        page = fetch_page(url, use_network_idle=True, timeout=35000)
        if page is None:
            page = fetch_page(url, use_network_idle=False, timeout=25000)
        text = get_text(page)
        if not text:
            print("    -> No text")
            continue
        kpl = parse_kpl(text)
        price = parse_clp_price(text)
        hp = parse_power_hp(text)
        kwh = parse_kwh100km(text)
        rng = parse_range_km(text)
        print(f"    -> kpl={kpl}, price={price}, hp={hp}, kwh={kwh}, range={rng}")
        scraped[name] = {
            "kpl": kpl,
            "price": price,
            "hp": hp,
            "kwh": kwh,
            "range": rng,
            "url": url,
        }
        time.sleep(1)


def scrape_ford():
    print("\n=== Scraping Ford Chile ===")
    urls = [
        ("Ford Territory", "https://www.ford.cl/suvs/territory.html"),
        ("Ford Ranger", "https://www.ford.cl/trucks/ranger.html"),
        ("Ford Bronco Sport", "https://www.ford.cl/suvs/bronco-sport.html"),
        ("Ford Explorer", "https://www.ford.cl/suvs/explorer.html"),
        ("Ford Escape", "https://www.ford.cl/suvs/escape.html"),
    ]
    for name, url in urls:
        print(f"  Fetching {name}...")
        page = fetch_page(url, use_network_idle=True, timeout=35000)
        if page is None:
            page = fetch_page(url, use_network_idle=False, timeout=25000)
        text = get_text(page)
        if not text:
            print("    -> No text")
            continue
        kpl = parse_kpl(text)
        price = parse_clp_price(text)
        hp = parse_power_hp(text)
        print(f"    -> kpl={kpl}, price={price}, hp={hp}")
        scraped[name] = {
            "kpl": kpl,
            "price": price,
            "hp": hp,
            "kwh": None,
            "range": None,
            "url": url,
        }
        time.sleep(1)


# =====================================================================
# RUN ALL SCRAPERS
# =====================================================================
scrape_toyota()
scrape_mazda()
scrape_hyundai()
scrape_kia()
scrape_chevrolet()
scrape_mg()
scrape_byd()
scrape_ford()

# Save raw scraped data for review
with open(
    "/Users/bastian/Documents/solomiro/backend/scraped_raw.json", "w", encoding="utf-8"
) as f:
    json.dump(scraped, f, ensure_ascii=False, indent=2)

print(f"\n\nTotal scraped entries: {len(scraped)}")
print("Saved to scraped_raw.json")

# =====================================================================
# UPDATE cars.json
# =====================================================================

# Mapping from scraped name -> cars.json id(s) to update
CAR_MAP = {
    "Toyota Corolla Cross Hybrid": [1],
    "Toyota Corolla Cross 2.0": [2],
    "Mazda CX-30": [3, 51],
    "Mazda CX-5": [18, 45],
    "Toyota RAV4 Hybrid": [13],
    "Toyota RAV4 2.5": [14, 44],
    "Hyundai Tucson": [15, 46],
    "Kia Sportage": [16, 47],
    "Toyota Corolla Sedan": [36, 48],
    "Toyota Yaris Sedan": [37, 52],
    "Mazda 3 Sedan": [39],
    "Hyundai Elantra": [43],
    "Chevrolet Tracker": [53],
    "BYD Song Pro": [7],
    "BYD Atto 3": [23],
    "BYD Dolphin": [29],
    "BYD Han EV": [30],
    "MG ZS": [8],
    "MG ZS EV": [32],
    "MG MG4": [31],
    "MG One PHEV": [28],
    "Kia Cerato": [41],
    "BYD Seal DM-i": [22],
    "BYD Tang EV": [34],
    "Toyota bZ4X": [],  # new car
    "Toyota Raize": [],  # new car
    "Toyota Hilux": [],  # new car
    "Toyota Yaris Cross Hybrid": [],  # new car
    "Toyota Fortuner": [],  # new car
    "Toyota Yaris Sedan Hybrid": [],  # new car
    "Mazda CX-3": [],
    "Mazda CX-60": [],
    "Mazda CX-90": [],
    "Mazda 3 Sport": [],
    "Mazda BT-50": [],
    "Hyundai Santa Fe": [],
    "Hyundai Accent": [],
    "Hyundai Ioniq 5": [],
    "Hyundai Ioniq 6": [],
    "Hyundai Creta": [],
    "Kia Sorento": [],
    "Kia Seltos": [],
    "Kia Stinger": [],
    "Kia EV6": [],
    "Kia Picanto": [],
    "Chevrolet Captiva": [],
    "Chevrolet Sail": [],
    "Chevrolet Onix": [],
    "Chevrolet Montana": [],
    "MG HS": [],
    "MG Marvel R": [],
    "Ford Territory": [],
    "Ford Ranger": [],
    "Ford Bronco Sport": [],
    "Ford Explorer": [],
    "Ford Escape": [],
}

# New car templates for cars not in JSON yet
NEW_CAR_TEMPLATES = {
    "Toyota bZ4X": {
        "brand": "Toyota",
        "model": "bZ4X",
        "year": 2025,
        "segment": "suv_compact",
        "condition": "new",
        "fuel_type": "electric",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 452,
        "tags": ["electric", "reliable", "suv"],
        "reliability_score": 8,
        "resale_score": 7,
        "parts_availability_score": 8,
        "maintenance_cost_score": 8,
        "safety_score": 9,
        "equipment_score": 8,
        "requires_home_charging": True,
        "not_recommended_if": "No puedes cargar en casa o priorizas autonomía máxima.",
        "consumption_kpl": None,
        "consumption_kwh100km": 18.0,
        "range_km": 450,
        "price_clp": 42900000,
        "power_hp": 204,
    },
    "Toyota Raize": {
        "brand": "Toyota",
        "model": "Raize",
        "year": 2025,
        "segment": "suv_compact",
        "condition": "new",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 369,
        "tags": ["compact", "efficient", "reliable"],
        "reliability_score": 8,
        "resale_score": 7,
        "parts_availability_score": 8,
        "maintenance_cost_score": 8,
        "safety_score": 7,
        "equipment_score": 7,
        "requires_home_charging": False,
        "not_recommended_if": "Necesitas más espacio o potencia.",
        "consumption_kpl": 16.7,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 11900000,
        "power_hp": 98,
    },
    "Toyota Hilux": {
        "brand": "Toyota",
        "model": "Hilux",
        "year": 2025,
        "segment": "pickup",
        "condition": "new",
        "fuel_type": "diesel",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": None,
        "tags": ["pickup", "reliable", "4x4", "diesel"],
        "reliability_score": 9,
        "resale_score": 9,
        "parts_availability_score": 9,
        "maintenance_cost_score": 7,
        "safety_score": 8,
        "equipment_score": 8,
        "requires_home_charging": False,
        "not_recommended_if": "Solo usas la camioneta en ciudad sin necesidad de 4x4.",
        "consumption_kpl": 11.1,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 29900000,
        "power_hp": 204,
    },
    "Toyota Yaris Cross Hybrid": {
        "brand": "Toyota",
        "model": "Yaris Cross Hybrid",
        "year": 2025,
        "segment": "suv_compact",
        "condition": "new",
        "fuel_type": "hybrid",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 270,
        "tags": ["hybrid", "efficient", "compact", "reliable"],
        "reliability_score": 9,
        "resale_score": 8,
        "parts_availability_score": 8,
        "maintenance_cost_score": 9,
        "safety_score": 8,
        "equipment_score": 7,
        "requires_home_charging": False,
        "not_recommended_if": "Necesitas mayor espacio de baúl o más potencia.",
        "consumption_kpl": 21.7,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 15900000,
        "power_hp": 116,
    },
    "Toyota Fortuner": {
        "brand": "Toyota",
        "model": "Fortuner",
        "year": 2025,
        "segment": "suv_large",
        "condition": "new",
        "fuel_type": "diesel",
        "transmission": "automatic",
        "seats": 7,
        "trunk_liters": 296,
        "tags": ["diesel", "4x4", "7seats", "reliable", "suv"],
        "reliability_score": 9,
        "resale_score": 8,
        "parts_availability_score": 8,
        "maintenance_cost_score": 7,
        "safety_score": 8,
        "equipment_score": 8,
        "requires_home_charging": False,
        "not_recommended_if": "Priorizas eficiencia o usas el auto en ciudad solamente.",
        "consumption_kpl": 10.5,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 42900000,
        "power_hp": 204,
    },
    "Toyota Yaris Sedan Hybrid": {
        "brand": "Toyota",
        "model": "Yaris Sedan Hybrid",
        "year": 2025,
        "segment": "sedan",
        "condition": "new",
        "fuel_type": "hybrid",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 286,
        "tags": ["hybrid", "efficient", "sedan", "reliable"],
        "reliability_score": 9,
        "resale_score": 8,
        "parts_availability_score": 8,
        "maintenance_cost_score": 9,
        "safety_score": 7,
        "equipment_score": 7,
        "requires_home_charging": False,
        "not_recommended_if": "Necesitas más espacio o un SUV.",
        "consumption_kpl": 23.8,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 15900000,
        "power_hp": 116,
    },
    "Hyundai Santa Fe": {
        "brand": "Hyundai",
        "model": "Santa Fe",
        "year": 2025,
        "segment": "suv_large",
        "condition": "new",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "seats": 7,
        "trunk_liters": 630,
        "tags": ["spacious", "7seats", "well_equipped", "suv"],
        "reliability_score": 8,
        "resale_score": 7,
        "parts_availability_score": 8,
        "maintenance_cost_score": 7,
        "safety_score": 9,
        "equipment_score": 9,
        "requires_home_charging": False,
        "not_recommended_if": "Priorizas máxima reventa o economía de combustible.",
        "consumption_kpl": 11.8,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 32900000,
        "power_hp": 277,
    },
    "Hyundai Creta": {
        "brand": "Hyundai",
        "model": "Creta",
        "year": 2025,
        "segment": "suv_compact",
        "condition": "new",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 402,
        "tags": ["compact_suv", "well_equipped", "value"],
        "reliability_score": 8,
        "resale_score": 7,
        "parts_availability_score": 8,
        "maintenance_cost_score": 7,
        "safety_score": 8,
        "equipment_score": 8,
        "requires_home_charging": False,
        "not_recommended_if": "Priorizas mayor espacio o reventa Toyota.",
        "consumption_kpl": 13.9,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 14900000,
        "power_hp": 115,
    },
    "Hyundai Ioniq 5": {
        "brand": "Hyundai",
        "model": "Ioniq 5",
        "year": 2025,
        "segment": "electric",
        "condition": "new",
        "fuel_type": "electric",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 527,
        "tags": ["electric", "premium", "fast_charging", "awd"],
        "reliability_score": 8,
        "resale_score": 7,
        "parts_availability_score": 7,
        "maintenance_cost_score": 8,
        "safety_score": 9,
        "equipment_score": 9,
        "requires_home_charging": True,
        "not_recommended_if": "No puedes cargar en casa o el precio supera tu presupuesto.",
        "consumption_kpl": None,
        "consumption_kwh100km": 17.5,
        "range_km": 481,
        "price_clp": 44900000,
        "power_hp": 225,
    },
    "Hyundai Ioniq 6": {
        "brand": "Hyundai",
        "model": "Ioniq 6",
        "year": 2025,
        "segment": "electric",
        "condition": "new",
        "fuel_type": "electric",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 401,
        "tags": ["electric", "premium", "aerodynamic", "efficient"],
        "reliability_score": 8,
        "resale_score": 7,
        "parts_availability_score": 7,
        "maintenance_cost_score": 8,
        "safety_score": 9,
        "equipment_score": 9,
        "requires_home_charging": True,
        "not_recommended_if": "No puedes cargar en casa o prefieres un SUV.",
        "consumption_kpl": None,
        "consumption_kwh100km": 14.9,
        "range_km": 614,
        "price_clp": 49900000,
        "power_hp": 239,
    },
    "Kia Sorento": {
        "brand": "Kia",
        "model": "Sorento",
        "year": 2025,
        "segment": "suv_large",
        "condition": "new",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "seats": 7,
        "trunk_liters": 604,
        "tags": ["spacious", "7seats", "well_equipped", "suv"],
        "reliability_score": 8,
        "resale_score": 7,
        "parts_availability_score": 8,
        "maintenance_cost_score": 7,
        "safety_score": 9,
        "equipment_score": 9,
        "requires_home_charging": False,
        "not_recommended_if": "Priorizas economía de combustible o reventa máxima.",
        "consumption_kpl": 11.1,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 34900000,
        "power_hp": 281,
    },
    "Kia Seltos": {
        "brand": "Kia",
        "model": "Seltos",
        "year": 2025,
        "segment": "suv_compact",
        "condition": "new",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 433,
        "tags": ["compact_suv", "well_equipped", "turbo"],
        "reliability_score": 8,
        "resale_score": 7,
        "parts_availability_score": 8,
        "maintenance_cost_score": 7,
        "safety_score": 8,
        "equipment_score": 8,
        "requires_home_charging": False,
        "not_recommended_if": "Priorizas reventa máxima o mayor espacio.",
        "consumption_kpl": 13.9,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 18900000,
        "power_hp": 146,
    },
    "Kia EV6": {
        "brand": "Kia",
        "model": "EV6",
        "year": 2025,
        "segment": "electric",
        "condition": "new",
        "fuel_type": "electric",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 480,
        "tags": ["electric", "premium", "sporty", "fast_charging"],
        "reliability_score": 8,
        "resale_score": 7,
        "parts_availability_score": 7,
        "maintenance_cost_score": 8,
        "safety_score": 9,
        "equipment_score": 9,
        "requires_home_charging": True,
        "not_recommended_if": "No puedes cargar en casa o el precio supera tu presupuesto.",
        "consumption_kpl": None,
        "consumption_kwh100km": 17.0,
        "range_km": 528,
        "price_clp": 44900000,
        "power_hp": 229,
    },
    "Chevrolet Captiva": {
        "brand": "Chevrolet",
        "model": "Captiva",
        "year": 2025,
        "segment": "suv_medium",
        "condition": "new",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "seats": 7,
        "trunk_liters": 226,
        "tags": ["7seats", "value", "chinese"],
        "reliability_score": 7,
        "resale_score": 5,
        "parts_availability_score": 7,
        "maintenance_cost_score": 7,
        "safety_score": 7,
        "equipment_score": 7,
        "requires_home_charging": False,
        "not_recommended_if": "Priorizas reventa o confiabilidad japonesa.",
        "consumption_kpl": 12.5,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 17900000,
        "power_hp": 148,
    },
    "Chevrolet Sail": {
        "brand": "Chevrolet",
        "model": "Sail",
        "year": 2025,
        "segment": "sedan",
        "condition": "new",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 450,
        "tags": ["budget_friendly", "sedan", "value"],
        "reliability_score": 7,
        "resale_score": 5,
        "parts_availability_score": 7,
        "maintenance_cost_score": 8,
        "safety_score": 7,
        "equipment_score": 6,
        "requires_home_charging": False,
        "not_recommended_if": "Priorizas reventa alta o confiabilidad superior.",
        "consumption_kpl": 15.4,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 10900000,
        "power_hp": 108,
    },
    "Chevrolet Onix": {
        "brand": "Chevrolet",
        "model": "Onix",
        "year": 2025,
        "segment": "sedan",
        "condition": "new",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 470,
        "tags": ["budget_friendly", "sedan", "value", "compact"],
        "reliability_score": 7,
        "resale_score": 5,
        "parts_availability_score": 7,
        "maintenance_cost_score": 8,
        "safety_score": 7,
        "equipment_score": 7,
        "requires_home_charging": False,
        "not_recommended_if": "Priorizas reventa alta o mayor confiabilidad.",
        "consumption_kpl": 16.1,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 11900000,
        "power_hp": 116,
    },
    "Ford Territory": {
        "brand": "Ford",
        "model": "Territory",
        "year": 2025,
        "segment": "suv_compact",
        "condition": "new",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 504,
        "tags": ["suv", "spacious", "american"],
        "reliability_score": 7,
        "resale_score": 6,
        "parts_availability_score": 7,
        "maintenance_cost_score": 6,
        "safety_score": 8,
        "equipment_score": 8,
        "requires_home_charging": False,
        "not_recommended_if": "Priorizas confiabilidad japonesa o reventa alta.",
        "consumption_kpl": 12.5,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 21900000,
        "power_hp": 143,
    },
    "Ford Ranger": {
        "brand": "Ford",
        "model": "Ranger",
        "year": 2025,
        "segment": "pickup",
        "condition": "new",
        "fuel_type": "diesel",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": None,
        "tags": ["pickup", "diesel", "4x4", "american"],
        "reliability_score": 7,
        "resale_score": 7,
        "parts_availability_score": 7,
        "maintenance_cost_score": 6,
        "safety_score": 8,
        "equipment_score": 8,
        "requires_home_charging": False,
        "not_recommended_if": "Solo usas en ciudad o priorizas economía de combustible.",
        "consumption_kpl": 11.8,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 28900000,
        "power_hp": 170,
    },
    "MG HS": {
        "brand": "MG",
        "model": "HS",
        "year": 2025,
        "segment": "suv_medium",
        "condition": "new",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 507,
        "tags": ["suv", "chinese", "value", "spacious"],
        "reliability_score": 7,
        "resale_score": 5,
        "parts_availability_score": 7,
        "maintenance_cost_score": 7,
        "safety_score": 7,
        "equipment_score": 8,
        "requires_home_charging": False,
        "not_recommended_if": "Priorizas reventa o confiabilidad probada.",
        "consumption_kpl": 12.5,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 18900000,
        "power_hp": 162,
    },
    "Mazda BT-50": {
        "brand": "Mazda",
        "model": "BT-50",
        "year": 2025,
        "segment": "pickup",
        "condition": "new",
        "fuel_type": "diesel",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": None,
        "tags": ["pickup", "diesel", "reliable", "4x4"],
        "reliability_score": 8,
        "resale_score": 7,
        "parts_availability_score": 7,
        "maintenance_cost_score": 7,
        "safety_score": 8,
        "equipment_score": 7,
        "requires_home_charging": False,
        "not_recommended_if": "Solo usas en ciudad o prefieres una camioneta americana.",
        "consumption_kpl": 11.1,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 25900000,
        "power_hp": 170,
    },
    "Mazda CX-60": {
        "brand": "Mazda",
        "model": "CX-60",
        "year": 2025,
        "segment": "suv_large",
        "condition": "new",
        "fuel_type": "gasoline",
        "transmission": "automatic",
        "seats": 5,
        "trunk_liters": 477,
        "tags": ["premium_feel", "sporty", "reliable", "suv"],
        "reliability_score": 8,
        "resale_score": 7,
        "parts_availability_score": 7,
        "maintenance_cost_score": 7,
        "safety_score": 9,
        "equipment_score": 9,
        "requires_home_charging": False,
        "not_recommended_if": "Priorizas reventa máxima o quieres 7 asientos.",
        "consumption_kpl": 12.5,
        "consumption_kwh100km": None,
        "range_km": None,
        "price_clp": 39900000,
        "power_hp": 284,
    },
}

# Load current cars.json
cars_path = "/Users/bastian/Documents/solomiro/backend/app/data/cars.json"
with open(cars_path, "r", encoding="utf-8") as f:
    cars = json.load(f)

cars_by_id = {c["id"]: c for c in cars}
max_id = max(c["id"] for c in cars)

updates_made = 0
new_cars_added = 0

for scraped_name, data in scraped.items():
    ids_to_update = CAR_MAP.get(scraped_name, [])

    for car_id in ids_to_update:
        if car_id not in cars_by_id:
            continue
        car = cars_by_id[car_id]
        changed = False

        if data.get("kpl") is not None and car["fuel_type"] not in ("electric",):
            old = car.get("consumption_kpl")
            car["consumption_kpl"] = data["kpl"]
            if old != data["kpl"]:
                print(
                    f"  Updated {car['name']}: consumption_kpl {old} -> {data['kpl']}"
                )
                changed = True

        if data.get("price") is not None:
            old = car.get("price_clp")
            car["price_clp"] = data["price"]
            if old != data["price"]:
                print(f"  Updated {car['name']}: price {old} -> {data['price']}")
                changed = True

        if data.get("hp") is not None:
            old = car.get("power_hp")
            car["power_hp"] = data["hp"]
            if old != data["hp"]:
                print(f"  Updated {car['name']}: power_hp {old} -> {data['hp']}")
                changed = True

        if data.get("kwh") is not None and car["fuel_type"] == "electric":
            old = car.get("consumption_kwh100km")
            car["consumption_kwh100km"] = data["kwh"]
            if old != data["kwh"]:
                print(
                    f"  Updated {car['name']}: consumption_kwh100km {old} -> {data['kwh']}"
                )
                changed = True

        if data.get("range") is not None and car["fuel_type"] == "electric":
            old = car.get("range_km")
            car["range_km"] = data["range"]
            if old != data["range"]:
                print(f"  Updated {car['name']}: range_km {old} -> {data['range']}")
                changed = True

        if changed:
            updates_made += 1

# Add new cars from scraped data
for scraped_name, data in scraped.items():
    template = NEW_CAR_TEMPLATES.get(scraped_name)
    if template is None:
        continue

    # Check if any data was found
    has_data = data.get("kpl") or data.get("price") or data.get("hp") or data.get("kwh")

    max_id += 1
    new_car = dict(template)
    new_car["id"] = max_id
    new_car["name"] = f"{template['brand']} {template['model']} {template['year']}"

    # Override with scraped data
    if data.get("kpl") and template.get("fuel_type") not in ("electric",):
        new_car["consumption_kpl"] = data["kpl"]
    if data.get("price"):
        new_car["price_clp"] = data["price"]
    if data.get("hp"):
        new_car["power_hp"] = data["hp"]
    if data.get("kwh"):
        new_car["consumption_kwh100km"] = data["kwh"]
    if data.get("range"):
        new_car["range_km"] = data["range"]

    cars.append(new_car)
    new_cars_added += 1
    print(f"  Added new car: {new_car['name']} (id={max_id})")

# Save updated cars.json
with open(cars_path, "w", encoding="utf-8") as f:
    json.dump(cars, f, ensure_ascii=False, indent=2)

print("\n=== SUMMARY ===")
print(f"Cars updated: {updates_made}")
print(f"New cars added: {new_cars_added}")
print(f"Total cars: {len(cars)}")
print(f"Saved to {cars_path}")

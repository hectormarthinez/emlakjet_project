from lxml import html
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode
import pandas as pd
import time
import tqdm
import concurrent.futures
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure session with connection pooling and retry strategy
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        backoff_factor=1
    )
    adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "Mozilla Firefox 12.0"})
    return session

# Function to extract provinces and districts
def get_provinces_districts():
    url = "https://www.drdatastats.com/turkiye-il-ve-ilceler-listesi/"
    session = create_session()
    response = session.get(url)
    
    provinces_dict = {}
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        
        for row in table.find_all('tr')[1:]:
            columns = row.find_all('td')
            province = columns[1].text.strip()
            district = columns[2].text.strip()
            province_ascii = unidecode(province).lower()
            district_ascii = unidecode(district).lower()
            
            if province_ascii not in provinces_dict:
                provinces_dict[province_ascii] = []
            provinces_dict[province_ascii].append(district_ascii)

    # Fix district names
    for province, districts in provinces_dict.items():
        provinces_dict[province] = [province + "-merkez" if d == "merkez" else "19-mayis" if d == "19 mayis" else d for d in districts]
    
    return provinces_dict

# Function to extract apartment data from a single listing page
def extract_apartment_data(apartment_link, session):
    try:
        apartment_response = session.get(apartment_link)
        apartment_tree = html.fromstring(apartment_response.content)
        
        # Extract price using regex to handle potential inconsistencies
        price_elements = apartment_tree.xpath("//*[@class='styles_price__6zH_9']/text()")
        price = price_elements[0].strip() if price_elements else ""
        
        # Extract location
        location_elements = apartment_tree.xpath("//*[@class='styles_location__Y01SC']/text()")
        if location_elements and " - " in location_elements[0]:
            location = location_elements[0].split(" - ")
            province_2 = location[0] if len(location) > 0 else ""
            district_2 = location[1] if len(location) > 1 else ""
            neighborhood = location[2] if len(location) > 2 else ""
        else:
            province_2, district_2, neighborhood = "", "", ""
        
        # Extract apartment info using a more efficient approach
        info = {}
        info_items = apartment_tree.xpath("//*[@id='ilan-hakkinda']/div/div/ul/li")
        for item in info_items:
            label = item.xpath(".//span[1]//text()")
            value = item.xpath(".//span[2]//text()")
            if label and value:
                key = label[0].strip()
                info[key] = value[0].strip()
        
        # Create apartment data dictionary with default values to avoid KeyError
        return {
            "price": price,
            "province": province_2,
            "district": district_2,
            "neighborhood": neighborhood,
            "announce_number": info.get("İlan Numarası", ""),
            "announce_publication_date": info.get("İlan Oluşturma Tarihi", ""),
            "announce_update_date": info.get("İlan Güncelleme Tarihi", ""),
            "type_1": info.get("Türü", ""),
            "type_2": info.get("Tipi", ""),
            "net_m2": info.get("Net Metrekare", ""),
            "brut_m2": info.get("Brüt Metrekare", ""),
            "number_rooms": info.get("Oda Sayısı", ""),
            "age": info.get("Binanın Yaşı", ""),
            "apartment_floor": info.get("Bulunduğu Kat", ""),
            "floors_of_building": info.get("Binanın Kat Sayısı", ""),
            "heating_type": info.get("Isıtma Tipi", ""),
            "usage_status": info.get("Kullanım Durumu", ""),
            "dues": info.get("Aidat", ""),
            "title_deed_status": info.get("Tapu Durumu", ""),
            "inside_side": info.get("Site İçerisinde", ""),
            "deposit": info.get("Depozito", ""),
            "number_bathrooms": info.get("Banyo Sayısı", ""),
            "balcony_status": info.get("Balkon Durumu", ""),
            "price_status": info.get("Fiyat Durumu", "")
        }
    except Exception as e:
        print(f"Error extracting data from {apartment_link}: {e}")
        return None

# Function to process a single page of apartment listings
def process_page(page_url, session):
    try:
        page_response = session.get(page_url)
        page_tree = html.fromstring(page_response.content)
        apartment_hrefs = page_tree.xpath("*//div[1]/div[4]/div[2]/div[3]//div/a/@href")
        
        # Use a list comprehension to build full URLs
        apartment_links = [f"https://www.emlakjet.com{href}" for href in apartment_hrefs]
        
        # Process apartment links with limited concurrency to avoid overwhelming the server
        apartments_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(extract_apartment_data, link, session) for link in apartment_links]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    apartments_data.append(result)
        
        return apartments_data
    except Exception as e:
        print(f"Error processing page {page_url}: {e}")
        return []

# Function to process a district
def process_district(province, district, session):
    base_url = f"https://www.emlakjet.com/kiralik-konut/{province}-{district}/emlakcidan/"
    try:
        response = session.get(base_url)
        tree = html.fromstring(response.content)
        soup = str(BeautifulSoup(response.content, "html.parser"))
        
        if "Aradığınız kriterlere uygun ilan bulunamadı." in soup:
            return []
        
        # Extract number of apartments more robustly
        num_apt_elements = tree.xpath("//*[@class='styles_strong__cM487']/text()")
        if not num_apt_elements:
            return []
            
        # Clean and parse the number
        num_text = num_apt_elements[0].replace(".", "")
        num_apartments = int(re.sub(r'\D', '', num_text)) if re.search(r'\d', num_text) else 0
        
        # Limit pages to reduce scraping time
        n_pages = min(((num_apartments // 30) + 1), 50)
        
        all_apartments_data = []
        # Create URLs for all pages at once
        page_urls = [f"{base_url}{page}" for page in range(1, n_pages+1)]
        
        # Process pages with limited concurrency
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_page, url, session) for url in page_urls]
            for future in tqdm.tqdm(concurrent.futures.as_completed(futures), 
                                   total=len(page_urls), 
                                   desc=f"Pages in {province.capitalize()}, {district.capitalize()}", 
                                   leave=False):
                result = future.result()
                all_apartments_data.extend(result)
                
        return all_apartments_data
    except Exception as e:
        print(f"Error processing district {province}-{district}: {e}")
        return []

def main():
    start_time = time.time()
    session = create_session()
    provinces_dict = get_provinces_districts()
    
    all_apartments_data = []
    
    # Process a limited number of provinces/districts to test optimization
    # Remove this limitation for full scraping
    province_count = 0
    max_provinces = 81  # Limit for testing
    
    for province in tqdm.tqdm(provinces_dict, desc="Provinces processed"):
        province_count += 1
        if province_count > max_provinces:
            break
            
        district_count = 0
        
        for district in provinces_dict[province]:
            district_count += 1
                
            # Add a small delay between districts to avoid rate limiting
            time.sleep(0.5)
            district_data = process_district(province, district, session)
            all_apartments_data.extend(district_data)
            
            # Save intermediate results periodically
            if len(all_apartments_data) % 100 == 0 and len(all_apartments_data) > 0:
                intermediate_df = pd.DataFrame(all_apartments_data)
                intermediate_df.to_excel(f"rented_apartments_intermediate_{len(all_apartments_data)}.xlsx", index=False)
    
    # Save final results
    apartments_dataframe = pd.DataFrame(all_apartments_data)
    apartments_dataframe.to_excel("apartments_for_rent.xlsx", index=False)
    
    end_time = time.time()
    print(f"Scraping completed in {end_time - start_time:.2f} seconds")
    print(f"Total apartments collected: {len(all_apartments_data)}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Split Taiwan pesticide data by individual pesticide codes
Create separate CSV files and download corresponding label images
Image paths shown as: /path_to_image | date
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import re
import argparse
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

class PesticideSplitter:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Referer': 'https://pesticide.aphia.gov.tw/'
        }
        self.session.headers.update(self.headers)
        self.base_url = "https://pesticide.aphia.gov.tw"
        
    def establish_session(self):
        """Establish session with Taiwan pesticide database"""
        try:
            response = self.session.get(f"{self.base_url}/information/Query/Pesticide")
            return response.status_code == 200
        except:
            return False
    
    def fetch_registration_data_with_images(self, pest_code):
        """Fetch registration data and extract image URLs using Taiwan pesticide registry"""
        url = f"{self.base_url}/information/Query/RegisterList"
        params = {
            'pestcd': pest_code,
            'page': '1',
            'pagesize': '100'
        }
        
        try:
            response = self.session.get(url, params=params)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the registration table
            table_div = soup.find('div', class_='table-data-list')
            if not table_div:
                return []
            
            table = table_div.find('table')
            if not table or not table.find('tbody'):
                return []
            
            registrations = []
            rows = table.find('tbody').find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 10:
                    # Extract permit number from link
                    permit_link = cells[0].find('a')
                    permit_number = permit_link.get_text(strip=True) if permit_link else cells[0].get_text(strip=True)
                    
                    # Extract regtid and regtno for image URL construction
                    regtid = '10'  # Default registration type
                    regtno = permit_number.replace('農藥製', '').replace('農藥進', '').replace('農藥原進', '').strip()
                    
                    # Clean up permit number format
                    if '農藥製' in permit_number:
                        regtid = '10'
                    elif '農藥進' in permit_number:
                        regtid = '11'
                    elif '農藥原進' in permit_number:
                        regtid = '12'
                    
                    # Construct image view URL
                    image_view_url = f"{self.base_url}/information/Query/RegisterViewMark/?regtid={regtid}&regtno={regtno}"
                    
                    # Extract other registration data
                    pest_name = cells[1].get_text(strip=True)
                    brand_name = cells[2].get_text(strip=True)
                    formulation = cells[3].get_text(strip=True)
                    concentration = cells[4].get_text(strip=True)
                    up_status = cells[5].get_text(strip=True)
                    mixture = cells[6].get_text(strip=True)
                    manufacturer = cells[7].get_text(strip=True)
                    foreign_mfg = cells[8].get_text(strip=True)
                    valid_date = cells[9].get_text(strip=True)
                    remarks = cells[10].get_text(separator='\\n', strip=True) if len(cells) > 10 else ''
                    
                    registration = {
                        'permit_number': permit_number,
                        'regtid': regtid,
                        'regtno': regtno,
                        'pesticide_name': pest_name,
                        'brand_name': brand_name,
                        'formulation_type': formulation,
                        'concentration': concentration,
                        'up_status': up_status,
                        'mixture': mixture,
                        'manufacturer': manufacturer,
                        'foreign_manufacturer': foreign_mfg,
                        'valid_date': valid_date,
                        'remarks': remarks,
                        'image_view_url': image_view_url,
                        'label_image_url': ''  # Will be populated by get_image_download_url
                    }
                    registrations.append(registration)
            
            return registrations
            
        except Exception as e:
            print(f"    Error fetching registration for {pest_code}: {e}")
            return []
    
    def get_image_download_url(self, regtid, regtno):
        """Get actual image download URL from the image view page"""
        try:
            view_url = f"{self.base_url}/information/Query/RegisterViewMark/"
            params = {'regtid': regtid, 'regtno': regtno}
            
            response = self.session.get(view_url, params=params)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for ViewmarkDownload links
            download_links = soup.find_all('a', href=True)
            for link in download_links:
                href = link.get('href', '')
                if 'ViewmarkDownload' in href:
                    return urljoin(self.base_url, href)
            
            # Alternative: look for image tags
            img_tags = soup.find_all('img', src=True)
            for img in img_tags:
                src = img.get('src', '')
                if any(ext in src.lower() for ext in ['.jpg', '.png', '.gif', '.jpeg']):
                    # Convert to download URL format
                    if 'url=' in src:
                        image_filename = src.split('url=')[-1]
                        download_url = f"{self.base_url}/information/Query/ViewmarkDownload/?type=mark&url={image_filename}"
                        return download_url
            
            return None
            
        except Exception as e:
            print(f"      Error getting image URL for {regtid}/{regtno}: {e}")
            return None
    
    def download_pesticide_image(self, image_url, pest_code, pest_name, permit_number, download_date):
        """Download and organize pesticide label image"""
        if not image_url:
            return None
            
        try:
            # Create pesticide-specific image directory with full name
            safe_pest_name = re.sub(r'[^\w\-_\u4e00-\u9fff]', '_', pest_name)
            folder_name = f"{pest_code}_{safe_pest_name}"
            image_dir = f"data/images/{folder_name}"
            os.makedirs(image_dir, exist_ok=True)
            
            # Get full URL if it's a relative path
            if image_url.startswith('/'):
                full_url = f"{self.base_url}{image_url}"
            elif not image_url.startswith('http'):
                full_url = urljoin(self.base_url, image_url)
            else:
                full_url = image_url
            
            print(f"    Downloading image: {full_url}")
            
            # Download image
            response = self.session.get(full_url)
            if response.status_code == 200:
                # Extract filename from URL
                if 'url=' in image_url:
                    original_filename = image_url.split('url=')[-1]
                elif '/' in image_url:
                    original_filename = image_url.split('/')[-1]
                else:
                    original_filename = f"{permit_number}.jpg"
                
                # Use original filename but ensure proper extension
                safe_filename = original_filename
                if '.' not in safe_filename:
                    safe_filename += '.jpg'
                
                # Extract permit number for organization
                number_match = re.search(r'(\d{5})', permit_number)
                if number_match:
                    permit_num = number_match.group(1)
                    # Keep original filename but prefix with permit number
                    name, ext = os.path.splitext(safe_filename)
                    safe_filename = f"{permit_num}_{safe_filename}"
                
                file_path = os.path.join(image_dir, safe_filename)
                
                # Save image
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"    Saved image: {file_path} ({len(response.content)} bytes)")
                
                # Return path in requested format: /absolute_path_to_image | date
                abs_path = os.path.abspath(file_path)
                return f"{abs_path} | {download_date}"
            else:
                print(f"    Failed to download image: HTTP {response.status_code}")
            
        except Exception as e:
            print(f"    Error downloading image {image_url}: {e}")
        
        return None
    
    def create_pesticide_csv(self, pest_code, pest_data, download_images=True):
        """Create individual CSV for one pesticide with all its data"""
        
        # Get basic pesticide info
        basic_info = pest_data['basic_info']
        pest_name = basic_info['pesticide_name']
        
        print(f"  Creating CSV for {pest_code}: {pest_name}")
        
        # Get fresh registration data with images
        fresh_registrations = self.fetch_registration_data_with_images(pest_code)
        
        # Combine existing and fresh data
        all_registrations = pest_data.get('registrations', []) + fresh_registrations
        
        # Remove duplicates based on permit number
        unique_registrations = {}
        for reg in all_registrations:
            permit_num = reg.get('permit_number', '')
            if permit_num and permit_num not in unique_registrations:
                unique_registrations[permit_num] = reg
        
        registrations = list(unique_registrations.values())
        
        # Create comprehensive records for this pesticide
        pesticide_records = []
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add basic pesticide information
        base_record = {
            'data_type': 'basic_info',
            'pesticide_code': pest_code,
            'pesticide_name': pest_name,
            'original_english_brand': basic_info.get('original_english_brand', ''),
            'primary_registrar': basic_info.get('primary_registrar', ''),
            'total_registrations': len(registrations),
            'data_source': 'Taiwan Pesticide Database',
            'fetch_time': current_date
        }
        pesticide_records.append(base_record)
        
        # Add registration records with images
        for i, registration in enumerate(registrations, 1):
            # Get image download URL and download if available
            image_path_with_date = ''
            if download_images:
                # First try to get the actual image download URL
                if registration.get('regtid') and registration.get('regtno'):
                    image_download_url = self.get_image_download_url(
                        registration['regtid'], 
                        registration['regtno']
                    )
                    registration['label_image_url'] = image_download_url
                    
                    if image_download_url:
                        image_path_with_date = self.download_pesticide_image(
                            image_download_url,
                            pest_code,
                            pest_name,
                            registration['permit_number'],
                            current_date.split()[0]  # Just the date part
                        )
            
            reg_record = {
                'data_type': 'registration',
                'sequence': i,
                'pesticide_code': pest_code,
                'pesticide_name': pest_name,
                'permit_number': registration['permit_number'],
                'brand_name': registration['brand_name'],
                'formulation_type': registration['formulation_type'],
                'concentration': registration['concentration'],
                'up_status': registration.get('up_status', ''),
                'mixture': registration.get('mixture', ''),
                'manufacturer': registration['manufacturer'],
                'foreign_manufacturer': registration.get('foreign_manufacturer', ''),
                'valid_date': registration['valid_date'],
                'remarks': registration.get('remarks', ''),
                'label_image_url': registration.get('label_image_url', ''),
                'local_image_path': image_path_with_date,
                'registration_status': 'active' if '廢止' not in str(registration.get('remarks', '')) else 'expired',
                'data_source': 'Taiwan Pesticide Database',
                'fetch_time': current_date
            }
            pesticide_records.append(reg_record)
        
        # Create DataFrame and save
        df = pd.DataFrame(pesticide_records)
        
        # Create pesticide-specific directory with full name
        safe_pest_name = re.sub(r'[^\\w\\-_\\u4e00-\\u9fff]', '_', pest_name)
        folder_name = f"{pest_code}_{safe_pest_name}"
        pest_dir = f"data/pesticides/{folder_name}"
        os.makedirs(pest_dir, exist_ok=True)
        
        # Save CSV
        csv_filename = f"{pest_code}_{safe_pest_name}.csv"
        csv_path = os.path.join(pest_dir, csv_filename)
        
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        return {
            'csv_path': csv_path,
            'record_count': len(pesticide_records),
            'registration_count': len(registrations),
            'image_count': len([r for r in pesticide_records if r.get('local_image_path')])
        }
    
    def load_pesticide_data(self):
        """Load existing pesticide data"""
        try:
            # Load basic pesticide list
            pesticide_list = pd.read_csv('data/regulatory/taiwan_pesticide_list.csv')
            
            # Load existing comprehensive data if available
            try:
                comprehensive_data = pd.read_csv('data/regulatory/taiwan_comprehensive_combined.csv')
            except FileNotFoundError:
                comprehensive_data = pd.DataFrame()
            
            # Organize data by pesticide code
            pesticide_data = {}
            
            for _, row in pesticide_list.iterrows():
                pest_code = row['代號']
                pest_name = row['農藥名稱']
                
                # Basic info
                basic_info = {
                    'pesticide_code': pest_code,
                    'pesticide_name': pest_name,
                    'original_english_brand': row.get('原始英文廠牌名稱', ''),
                    'primary_registrar': row.get('登記廠商', '')
                }
                
                # Get existing registration data if available
                registrations = []
                if not comprehensive_data.empty:
                    pest_regs = comprehensive_data[
                        (comprehensive_data['pesticide_code'] == pest_code) & 
                        (comprehensive_data['data_type'] == 'pesticide_with_registration')
                    ]
                    
                    for _, reg_row in pest_regs.iterrows():
                        registrations.append({
                            'permit_number': reg_row.get('permit_number', ''),
                            'brand_name': reg_row.get('brand_name', ''),
                            'formulation_type': reg_row.get('formulation_type', ''),
                            'concentration': reg_row.get('concentration', ''),
                            'manufacturer': reg_row.get('manufacturer', ''),
                            'valid_date': reg_row.get('valid_date', ''),
                            'remarks': reg_row.get('remarks', '')
                        })
                
                pesticide_data[pest_code] = {
                    'basic_info': basic_info,
                    'registrations': registrations
                }
            
            return pesticide_data
            
        except FileNotFoundError as e:
            print(f"Error loading pesticide data: {e}")
            return {}

def main():
    parser = argparse.ArgumentParser(description='Split pesticides into individual CSV files with images')
    parser.add_argument('-l', '--limit', type=int,
                        help='Limit number of pesticides to process (for testing)')
    parser.add_argument('--codes', nargs='+',
                        help='Process specific pesticide codes only (e.g., A001 F005)')
    parser.add_argument('--no-images', action='store_true',
                        help='Skip downloading label images')
    parser.add_argument('--images-only', action='store_true',
                        help='Only download images, skip if CSV already exists')
    
    args = parser.parse_args()
    
    print("=== Taiwan Pesticide Data Splitter with Images ===")
    
    # Initialize splitter
    splitter = PesticideSplitter()
    
    print("Establishing session...")
    if not splitter.establish_session():
        print("Warning: Could not establish session. Image download may fail.")
    
    # Load pesticide data
    print("Loading pesticide data...")
    pesticide_data = splitter.load_pesticide_data()
    
    if not pesticide_data:
        print("No pesticide data found!")
        return
    
    # Filter pesticides to process
    if args.codes:
        pesticides_to_process = {code: pesticide_data[code] for code in args.codes if code in pesticide_data}
        print(f"Processing specific codes: {list(pesticides_to_process.keys())}")
    else:
        pesticides_to_process = pesticide_data
        print(f"Processing all {len(pesticides_to_process)} pesticides")
    
    # Apply limit
    if args.limit:
        pesticides_to_process = dict(list(pesticides_to_process.items())[:args.limit])
        print(f"Limited to first {len(pesticides_to_process)} pesticides")
    
    # Process each pesticide
    download_images = not args.no_images
    results = []
    
    print(f"\\nStarting individual pesticide processing...")
    print(f"Image download: {'Enabled' if download_images else 'Disabled'}")
    
    for i, (pest_code, pest_data) in enumerate(pesticides_to_process.items(), 1):
        print(f"{i}/{len(pesticides_to_process)}: {pest_code}")
        
        try:
            # Check if CSV already exists and we're in images-only mode
            pest_dir = f"data/pesticides/{pest_code}"
            if args.images_only and os.path.exists(pest_dir):
                csv_files = [f for f in os.listdir(pest_dir) if f.endswith('.csv')]
                if csv_files:
                    print(f"  Skipping {pest_code} - CSV already exists")
                    continue
            
            result = splitter.create_pesticide_csv(pest_code, pest_data, download_images)
            results.append(result)
            
            # Respectful delay
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  Error processing {pest_code}: {e}")
            continue
    
    # Summary
    print(f"\\n=== Processing Complete ===")
    print(f"Pesticides processed: {len(results)}")
    
    if results:
        total_records = sum(r['record_count'] for r in results)
        total_registrations = sum(r['registration_count'] for r in results)
        total_images = sum(r['image_count'] for r in results)
        
        print(f"Total CSV records: {total_records}")
        print(f"Total registrations: {total_registrations}")
        print(f"Total images downloaded: {total_images}")
        print(f"Data saved to: data/pesticides/[CODE_NAME]/")
        print(f"Images saved to: data/images/[CODE_NAME]/")
        
        # Show sample results
        print(f"\\nSample results:")
        for result in results[:5]:
            csv_name = os.path.basename(result['csv_path'])
            print(f"  {csv_name}: {result['record_count']} records, {result['image_count']} images")

if __name__ == '__main__':
    main()
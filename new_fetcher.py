#!/usr/bin/env python3
"""
New fetcher for the PPM system at otserv2.acri.gov.tw
This script extracts crop pesticide data from the new Taiwan government website
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import argparse
import os
import time
import glob
from datetime import datetime
from io import StringIO

class PPMDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
        }
        self.session.headers.update(self.headers)
        self.base_url = "https://otserv2.acri.gov.tw/PPM"
        
    def establish_session(self):
        """Establish session and access the system"""
        print("Establishing session...")
        
        # Access the system with full functionality
        self.session.get(f"{self.base_url}/Index.aspx")
        self.session.get(f"{self.base_url}/Menu.aspx?ASParam=JTdkWFBYJTE0JTE4NjZpdA==")
        self.session.get(f"{self.base_url}/PLC02.aspx")
        
        print("Session established")
    
    def get_existing_crops(self, base_filename):
        """Get list of crops that already have data files"""
        existing_crops = set()
        
        # Check data/usage/ folder for existing files
        pattern = f"data/usage/*_{base_filename}"
        existing_files = glob.glob(pattern)
        
        for file_path in existing_files:
            # Extract crop name from filename
            filename = os.path.basename(file_path)
            # Remove the base_filename suffix to get crop name
            crop_name = filename.replace(f"_{base_filename}", "")
            existing_crops.add(crop_name)
        
        print(f"Found {len(existing_crops)} existing crop files")
        return existing_crops
    
    def get_crop_list(self):
        """Extract the crop list and their URLs"""
        print("Fetching crop list...")
        
        response = self.session.get(f"{self.base_url}/PLC02.aspx")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all crop links
        crop_links = []
        for link in soup.find_all(['div', 'a'], onclick=True):
            onclick = link.get('onclick', '')
            if 'PLC0101.aspx?ASParam=' in onclick:
                # Extract the URL
                url_match = re.search(r"location\.href='([^']+)'", onclick)
                if url_match:
                    url = url_match.group(1)
                    # Get the crop name from the text
                    crop_name = link.text.strip()
                    if crop_name:
                        crop_links.append({
                            'name': crop_name,
                            'url': f"{self.base_url}/{url}"
                        })
        
        print(f"Found {len(crop_links)} crop entries")
        return crop_links
    
    def parse_table_with_tolerance(self, soup):
        """Parse table data including hidden tolerance columns"""
        all_data = []
        
        # Use pandas to get the main pesticide table structure, then enhance with tolerance data
        try:
            import pandas as pd
            from io import StringIO
            
            # Get the table structure using pandas
            dfs = pd.read_html(StringIO(str(soup)))
            pesticide_df = None
            
            # Find the pesticide table
            for i, df in enumerate(dfs):
                if df.shape[0] > 1 and df.shape[1] > 3:
                    if any('藥劑' in str(col) for col in df.columns):
                        pesticide_df = df
                        break
            
            if pesticide_df is None:
                return all_data
            
            print(f"    Found pesticide table with {len(pesticide_df)} rows and {len(pesticide_df.columns)} columns")
            
            # Get tolerance header
            tolerance_header = soup.find('th', {'id': lambda x: x and 'tolerance' in x.lower()})
            tolerance_column_name = "殘留容許量(ppm)"
            if tolerance_header:
                tolerance_text = tolerance_header.get_text(strip=True)
                if tolerance_text:
                    tolerance_column_name = tolerance_text
            
            # Find all tolerance data cells
            tolerance_cells = soup.find_all('td', {'id': lambda x: x and 'tolerance_td' in x.lower()})
            print(f"    Found {len(tolerance_cells)} tolerance data cells")
            
            # Create tolerance data mapping by extracting row numbers from IDs
            tolerance_data = {}
            for cell in tolerance_cells:
                cell_id = cell.get('id', '')
                tolerance_text = cell.get_text(strip=True)
                
                # Extract row number from ID like "Tolerance_td39"
                import re
                match = re.search(r'tolerance_td(\d+)', cell_id.lower())
                if match:
                    row_num = int(match.group(1))
                    tolerance_data[row_num] = tolerance_text
            
            # Convert pandas DataFrame to list of dictionaries and add tolerance data
            for i, (idx, row) in enumerate(pesticide_df.iterrows()):
                row_dict = row.to_dict()
                
                # Try to find corresponding tolerance data
                # The tolerance row numbers seem to start from a base number
                tolerance_text = ""
                for tolerance_row_num, tolerance_value in tolerance_data.items():
                    # Try different mapping strategies
                    if tolerance_row_num - 38 == i:  # Adjust base offset as needed
                        tolerance_text = tolerance_value
                        break
                    elif tolerance_row_num - 39 == i:
                        tolerance_text = tolerance_value
                        break
                    elif tolerance_row_num - len(tolerance_data) + len(pesticide_df) == i:
                        tolerance_text = tolerance_value
                        break
                
                row_dict[tolerance_column_name] = tolerance_text
                all_data.append(row_dict)
            
            if tolerance_data:
                print(f"    Successfully added tolerance data to {len([r for r in all_data if r.get(tolerance_column_name)])} rows")
            
            return all_data
            
        except Exception as e:
            print(f"    Error in enhanced parsing: {e}")
            return all_data
    
    def fetch_crop_pesticides(self, crop_url, crop_name, base_filename):
        """Fetch pesticide data for a specific crop and save immediately"""
        print(f"  Fetching data for: {crop_name}")
        
        try:
            response = self.session.get(crop_url)
            
            if response.status_code != 200:
                print(f"    Error: HTTP {response.status_code}")
                return 0
            
            # Parse HTML to get both regular and tolerance data
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try custom parsing first to get tolerance data
            custom_data = self.parse_table_with_tolerance(soup)
            
            if custom_data:
                print(f"    Found {len(custom_data)} records with custom parsing")
                
                # Convert to DataFrame
                df = pd.DataFrame(custom_data)
                
                # Add metadata
                df['作物名稱'] = crop_name
                df['資料來源URL'] = crop_url
                df['擷取時間'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Save immediately to usage folder
                os.makedirs('data/usage', exist_ok=True)
                safe_crop_name = re.sub(r'[^\w\-_\u4e00-\u9fff]', '_', crop_name)
                filename = f"data/usage/{safe_crop_name}_{base_filename}"
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"    Saved {len(df)} records to {filename}")
                
                return len(df)
            
            # Fallback to pandas HTML parsing
            try:
                dfs = pd.read_html(StringIO(response.text))
                
                # Look for the pesticide data table (usually has columns like 藥劑名稱)
                for i, df in enumerate(dfs):
                    if df.shape[0] > 1 and df.shape[1] > 3:  # Non-empty table with multiple columns
                        if any('藥劑' in str(col) for col in df.columns):
                            print(f"    Found pesticide table: {df.shape}")
                            
                            # Add metadata
                            df['作物名稱'] = crop_name
                            df['資料來源URL'] = crop_url
                            df['擷取時間'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Save immediately to usage folder
                            os.makedirs('data/usage', exist_ok=True)
                            safe_crop_name = re.sub(r'[^\w\-_\u4e00-\u9fff]', '_', crop_name)
                            filename = f"data/usage/{safe_crop_name}_{base_filename}"
                            df.to_csv(filename, index=False, encoding='utf-8-sig')
                            print(f"    Saved {len(df)} records to {filename}")
                            
                            return len(df)
                
            except Exception as e:
                print(f"    Error parsing tables: {e}")
                
        except Exception as e:
            print(f"    Error fetching {crop_url}: {e}")
        
        return 0
    
    def save_data_by_crop(self, all_data, base_filename):
        """Save data for each crop to separate CSV files"""
        if not all_data:
            return 0
        
        total_records = 0
        for df in all_data:
            if not df.empty and '作物名稱' in df.columns:
                crop_name = df['作物名稱'].iloc[0]
                # Sanitize filename
                safe_crop_name = re.sub(r'[^\w\-_\u4e00-\u9fff]', '_', crop_name)
                filename = f"data/{safe_crop_name}_{base_filename}"
                
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"Saved {len(df)} records to {filename}")
                total_records += len(df)
        
        return total_records

def main():
    parser = argparse.ArgumentParser(description='Fetch pesticide data from Taiwan PPM system')
    parser.add_argument('-o', '--output', default='pesticide_data.csv',
                        help='Output CSV filename')
    parser.add_argument('-l', '--limit', type=int, default=10,
                        help='Limit number of crops to process (for testing)')
    parser.add_argument('--full', action='store_true',
                        help='Process all crops (ignores limit)')
    parser.add_argument('--force', action='store_true',
                        help='Force re-download all crops (ignore existing files)')
    
    args = parser.parse_args()
    
    # Create directories (will be handled in fetch_crop_pesticides method)
    
    # Initialize fetcher
    fetcher = PPMDataFetcher()
    fetcher.establish_session()
    
    # Get crop list
    crop_list = fetcher.get_crop_list()
    
    if not crop_list:
        print("No crops found!")
        return
    
    # Filter out existing crops unless force is specified
    if args.force:
        crops_to_process = crop_list
        print(f"Total crops: {len(crop_list)}")
        print(f"Force mode: Will re-download all crops")
    else:
        # Get existing crops to avoid duplicates
        existing_crops = fetcher.get_existing_crops(args.output)
        
        # Filter out crops that already have data
        new_crops = []
        for crop in crop_list:
            # Sanitize crop name same way as in fetch_crop_pesticides
            safe_crop_name = re.sub(r'[^\w\-_\u4e00-\u9fff]', '_', crop['name'])
            if safe_crop_name not in existing_crops:
                new_crops.append(crop)
        
        print(f"Total crops: {len(crop_list)}")
        print(f"Already processed: {len(existing_crops)}")
        print(f"New crops to process: {len(new_crops)}")
        
        crops_to_process = new_crops
    
    # Apply limit if not full mode
    if not args.full:
        crops_to_process = crops_to_process[:args.limit]
        print(f"Processing first {len(crops_to_process)} crops (use --full for all)...")
    else:
        print(f"Processing all {len(crops_to_process)} crops...")
    
    # Fetch data for each crop
    success_count = 0
    total_records = 0
    
    for i, crop in enumerate(crops_to_process, 1):
        print(f"{i}/{len(crops_to_process)}: {crop['name']}")
        
        records = fetcher.fetch_crop_pesticides(crop['url'], crop['name'], args.output)
        if records > 0:
            success_count += 1
            total_records += records
        
        # Small delay to be respectful
        time.sleep(0.5)
    
    # Final summary
    print(f"\n=== Summary ===")
    print(f"Crops processed: {len(crops_to_process)}")
    print(f"Successful: {success_count}")
    print(f"Total records: {total_records}")
    print(f"Files saved to data/ directory, named by crop category")

if __name__ == '__main__':
    main()
"""
RimTours Tour Data Integration System
Arctic ↔ WordPress ACF ↔ Outline ↔ PostgreSQL Sync
"""
import json
import pandas as pd
import psycopg2
import requests
from dotenv import load_dotenv
import os
from datetime import datetime
import re

# Load environment variables
load_dotenv()

class RimToursDataSync:
    def __init__(self):
        self.postgres_conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        
        self.outline_headers = {
            "Authorization": f"Bearer {os.getenv('OUTLINE_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        self.arctic_headers = {
            "Authorization": f"Bearer {os.getenv('ARCTIC_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        self.outline_url = os.getenv('OUTLINE_URL', 'https://your-outline-instance.com/api')
        self.arctic_url = os.getenv('ARCTIC_URL', 'https://your-arctic-system.com/api')
    
    def sync_arctic_to_postgres(self):
        """Sync latest data from Arctic to PostgreSQL"""
        print("🔄 Syncing Arctic → PostgreSQL...")
        
        # Load Arctic data from CSV (or API)
        df_arctic = pd.read_csv('data/input/arctic_triptype.csv', dtype=str)
        df_pricing = pd.read_csv('data/input/arctic_pricing_final.csv', dtype=str)
        
        cur = self.postgres_conn.cursor()
        
        for idx, row in df_arctic.iterrows():
            # Get pricing for this tour
            pricing_rows = df_pricing[df_pricing['Arctic_ID'] == row.get('id')]
            price = "TBD"
            if not pricing_rows.empty:
                std_price = pricing_rows[pricing_rows['Price_Name'].str.contains('Standard|Adult', case=False, na=False)]
                if not std_price.empty:
                    price = f"${float(std_price.iloc[0]['Amount']):,.0f}"
            
            # Insert/update in PostgreSQL
            cur.execute("""
                INSERT INTO tours (master_name, arctic_id, shortname, price, duration, business_group, variant_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (arctic_id) 
                DO UPDATE SET
                    master_name = EXCLUDED.master_name,
                    shortname = EXCLUDED.shortname,
                    price = EXCLUDED.price,
                    duration = EXCLUDED.duration,
                    business_group = EXCLUDED.business_group,
                    variant_type = EXCLUDED.variant_type,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                row.get('name', ''),
                row.get('id'),
                row.get('shortname', ''),
                price,
                row.get('duration', ''),
                row.get('businessgroupid', ''),
                'Standard' if row.get('businessgroupid', '') not in ['9','10','11','12'] else 'Private'
            ))
        
        self.postgres_conn.commit()
        cur.close()
        print("✅ Arctic → PostgreSQL sync completed")
    
    def sync_wordpress_to_postgres(self):
        """Sync WordPress ACF data to PostgreSQL"""
        print("🔄 Syncing WordPress ACF → PostgreSQL...")

        df_web = pd.read_csv('data/input/website_export.csv', dtype=str)
        cur = self.postgres_conn.cursor()

        for idx, row in df_web.iterrows():
            # Extract ACF field data
            meta = {
                'subtitle': self.get_val(['subtitle', '_subtitle'], row),
                'region': self.get_val(['region', '_region', 'Region'], row),
                'skill_level': self.get_val(['skill_level', '_skill_level'], row),
                'season': self.get_val(['season', '_season'], row),
                'short_description': self.get_val(['short_description', '_short_description', 'Excerpt'], row),
                'long_description': self.get_val(['description', '_description', 'Content'], row),
                'departs': self.get_val(['departs', '_departs'], row),
                'distance': self.get_val(['distance', '_distance'], row),
                'standard_price': self.get_val(['standard_price', '_standard_price'], row),
                'bike_rental': self.get_val(['bike_rental', '_bike_rental'], row),
                'camp_rental': self.get_val(['camp_rental', '_camp_rental'], row),
                'shuttle_fee': self.get_val(['shuttle_fee', '_shuttle_fee'], row),
                'special_notes': self.get_val(['special_notes', '_special_notes'], row),
                'dates': self.get_val(['dates', '_dates'], row),
                'reservation_link': self.get_val(['reservation_link', '_reservation_link'], row),
                'images': self.extract_image_filenames(self.get_val(['Image URL', 'Featured Image'], row))
            }

            # Get website URL from the links data if available
            website_url = self.get_website_url_for_tour(row.get('Title', ''))

            # Update website_data table
            cur.execute("""
                INSERT INTO website_data
                (website_id, master_name, subtitle, region, skill_level, season,
                 short_description, long_description, departs_from, distance,
                 pricing_info, fees_info, special_notes, dates_available,
                 reservation_link, images_filenames, website_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (website_id)
                DO UPDATE SET
                    subtitle = EXCLUDED.subtitle,
                    region = EXCLUDED.region,
                    skill_level = EXCLUDED.skill_level,
                    season = EXCLUDED.season,
                    short_description = EXCLUDED.short_description,
                    long_description = EXCLUDED.long_description,
                    departs_from = EXCLUDED.departs_from,
                    distance = EXCLUDED.distance,
                    pricing_info = EXCLUDED.pricing_info,
                    special_notes = EXCLUDED.special_notes,
                    dates_available = EXCLUDED.dates_available,
                    reservation_link = EXCLUDED.reservation_link,
                    images_filenames = EXCLUDED.images_filenames,
                    website_url = EXCLUDED.website_url,
                    last_synced = CURRENT_TIMESTAMP
            """, (
                row.get('ID'),
                row.get('Title', ''),
                meta['subtitle'],
                meta['region'],
                meta['skill_level'],
                meta['season'],
                meta['short_description'],
                meta['long_description'],
                meta['departs'],
                meta['distance'],
                meta['standard_price'],
                json.dumps({
                    'bike_fee': meta['bike_rental'],
                    'camp_fee': meta['camp_rental'],
                    'shuttle_fee': meta['shuttle_fee']
                }),
                meta['special_notes'],
                meta['dates'],
                meta['reservation_link'],
                meta['images'],
                website_url
            ))

        self.postgres_conn.commit()
        cur.close()
        print("✅ WordPress ACF → PostgreSQL sync completed")

    def load_website_links(self):
        """Load website links from CSV file"""
        try:
            df_links = pd.read_csv('data/input/rimtours_links.csv')
            return df_links
        except FileNotFoundError:
            print("⚠️ Website links file not found, proceeding without URL mapping")
            return pd.DataFrame()

    def get_website_url_for_tour(self, tour_name):
        """Find the website URL for a given tour name"""
        df_links = self.load_website_links()
        if df_links.empty:
            return None

        # Clean the tour name for matching
        clean_tour_name = tour_name.lower().replace('/', '').replace('-', ' ').strip()

        # Look for matches in the links data
        for _, row in df_links.iterrows():
            link_text = row['text'].lower()
            # Direct match
            if clean_tour_name in link_text or link_text in clean_tour_name:
                return row['url']
            # Partial match with common variations
            if self.calculate_similarity(clean_tour_name, link_text) > 0.7:
                return row['url']

        return None

    def calculate_similarity(self, str1, str2):
        """Calculate similarity between two strings"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1, str2).ratio()
    
    def sync_postgres_to_outline(self):
        """Generate markdown and upload to Outline via API"""
        print("🔄 Syncing PostgreSQL → Outline...")
        
        cur = self.postgres_conn.cursor()
        
        # Get all tours with Arctic priority
        cur.execute("""
            SELECT
                t.id as tour_internal_id,
                t.master_name,
                COALESCE(t.shortname, 'N/A') as authoritative_shortname,
                COALESCE(t.price, 'TBD') as authoritative_price,
                t.duration,
                t.variant_type,
                w.subtitle,
                w.region,
                w.skill_level,
                w.season,
                w.short_description,
                w.long_description,
                w.images_filenames,
                w.reservation_link,
                w.special_notes,
                COALESCE(t.updated_at, w.last_synced) as last_updated,
                w.website_url
            FROM tours t
            LEFT JOIN website_data w ON t.arctic_id = w.website_id  -- This join might need adjustment
        """)
        
        tours = cur.fetchall()
        
        for tour in tours:
            markdown_content = self.generate_arctic_first_markdown(tour)
            
            # Find or create document in Outline
            existing_doc_id = self.find_outline_document(tour[1])  # master_name
            
            if existing_doc_id:
                # Update existing document
                response = requests.post(
                    f"{self.outline_url}/documents.update",
                    headers=self.outline_headers,
                    json={
                        "id": existing_doc_id,
                        "title": tour[1],  # master_name
                        "text": markdown_content,
                        "publish": True
                    }
                )
                action = "updated"
            else:
                # Create new document in appropriate collection
                collection_id = self.get_outline_collection(tour[1])
                response = requests.post(
                    f"{self.outline_url}/documents.create",
                    headers=self.outline_headers,
                    json={
                        "collection": collection_id,
                        "title": tour[1],  # master_name
                        "text": markdown_content,
                        "publish": True
                    }
                )
                action = "created"
            
            if response.status_code == 200:
                print(f"✅ {action.capitalize()} {tour[1]} in Outline")
            else:
                print(f"❌ Failed to {action} {tour[1]}: {response.text}")
        
        cur.close()
        print("✅ PostgreSQL → Outline sync completed")
    
    def sync_outline_changes_to_arctic(self):
        """Detect and sync changes from Outline back to Arctic"""
        print("🔄 Syncing Outline → Arctic...")
        
        # Get all documents from Outline
        response = requests.get(f"{self.outline_url}/documents.list", headers=self.outline_headers)
        
        if response.status_code == 200:
            outline_docs = response.json().get('data', [])
            
            for doc in outline_docs:
                # Get document content
                doc_response = requests.get(
                    f"{self.outline_url}/documents.info",
                    headers=self.outline_headers,
                    params={"id": doc['id']}
                )
                
                if doc_response.status_code == 200:
                    doc_data = doc_response.json()
                    outline_content = doc_data['data']['text']
                    outline_title = doc_data['data']['title']
                    
                    # Check if this is a tour document (has Arctic Code)
                    if "Arctic Code" in outline_content:
                        arctic_code_match = re.search(r'\|\s*\*\*(.*?)\*\*\s*\|', outline_content)
                        if arctic_code_match:
                            arctic_shortname = arctic_code_match.group(1).strip()
                            
                            # Extract new content from Outline
                            new_description = self.extract_description_from_markdown(outline_content)
                            new_subtitle = self.extract_subtitle_from_markdown(outline_content)
                            
                            # Update Arctic system
                            try:
                                arctic_response = requests.put(
                                    f"{self.arctic_url}/tours/shortname/{arctic_shortname}",
                                    headers=self.arctic_headers,
                                    json={
                                        "description": new_description,
                                        "subtitle": new_subtitle,
                                        "sync_source": "outline_update"
                                    }
                                )
                                
                                if arctic_response.status_code == 200:
                                    print(f"✅ Updated Arctic with Outline changes for {outline_title}")
                                else:
                                    print(f"⚠️ Arctic update failed: {arctic_response.text}")
                                    
                            except Exception as e:
                                print(f"❌ Error updating Arctic: {e}")
        
        print("✅ Outline → Arctic sync completed")
    
    def daily_sync(self):
        """Complete daily sync process"""
        print(f"🔄 Starting daily sync at {datetime.now()}")
        
        self.sync_arctic_to_postgres()
        self.sync_wordpress_to_postgres()
        self.sync_postgres_to_outline()
        
        print("✅ Daily sync completed successfully!")
    
    def get_val(self, cols, row):
        """Helper to get value from multiple possible column names"""
        for c in cols:
            if c in row and not pd.isna(row[c]):
                return str(row[c])
        return ""
    
    def extract_image_filenames(self, url_string):
        """Extract image filenames from URL string"""
        if pd.isna(url_string) or str(url_string).strip() == "":
            return ""
        
        urls = str(url_string).split('|')
        filenames = [url.split('/')[-1] for url in urls if url.strip()]
        return ", ".join(filenames[:6])
    
    def generate_arctic_first_markdown(self, tour):
        """Generate markdown with Arctic data prioritized"""
        fees_info = {"bike_fee": "N/A", "camp_fee": "N/A", "shuttle_fee": "N/A"}

        # Extract website URL from the tour data (assuming it's in tour[18] based on updated query)
        website_url = tour[18] if len(tour) > 18 else None

        markdown = f"""# {tour[1]}

<!-- SYSTEM METADATA -->
| Arctic Code | System Status | Last Updated | Website URL |
| :--- | :--- | :--- | :--- |
| **{tour[2]}** | Synced | {tour[15].strftime('%Y-%m-%d %H:%M') if tour[15] else datetime.now().strftime('%Y-%m-%d %H:%M')} | {website_url or 'N/A'} |

---

## 1. The Shared DNA
**Subtitle:** {tour[6] or ''}
**Region:** {tour[7] or ''}
**Skill Level:** {tour[8] or ''}
**Season:** {tour[9] or ''}

**Short Description:**
> {tour[10] or ''}

**Long Description:**
> {tour[11][:1500] if tour[11] else ''}...

**Images (Filenames):**
`{tour[12] or 'No images found'}`

## 💵 Pricing Information (Arctic-Authoritative)
**Standard Price:** {tour[3]}  # Arctic price (authoritative!)
**Duration:** {tour[4] or 'N/A'}
**Type:** {tour[5] or 'N/A'}

## 🌐 Website Links
"""

        if website_url:
            markdown += f"- **Tour Page:** [{website_url}]({website_url})\n"

        if tour[16]:  # reservation link
            markdown += f"- **Reservation Link:** [{tour[16]}]({tour[16]})\n"

        markdown += f"""

## 💰 Fees & Logistics
| Item | Cost / Details |
| :--- | :--- | :--- |
| **Bike Rental** | {fees_info.get('bike_fee', 'N/A')} |
| **Camp Kit** | {fees_info.get('camp_fee', 'N/A')} |
| **Shuttle Service** | {fees_info.get('shuttle_fee', 'N/A')} |

## 📋 Additional Information
**Departs From:** {tour[13] or ''}
**Distance:** {tour[14] or ''}
**Special Notes:** {tour[17] or ''}

---

## 2. Arctic Configurations (SKUs)
| Variant Name | Arctic ID | Price | Duration | Type |
| :--- | :--- | :--- | :--- | :--- |
| **{tour[1]}** | {tour[2]} | {tour[3]} | {tour[4]} | {tour[5]} |

## 3. Full Content
{tour[11] or ''}
"""
        return markdown
    
    def find_outline_document(self, title):
        """Find existing document by title"""
        response = requests.get(
            f"{self.outline_url}/documents.list",
            headers=self.outline_headers
        )
        
        if response.status_code == 200:
            docs = response.json().get('data', [])
            for doc in docs:
                if doc['title'] == title:
                    return doc['id']
        return None
    
    def get_outline_collection(self, tour_name):
        """Map tour names to Outline collection IDs"""
        if "Day" in tour_name:
            return os.getenv('OUTLINE_DAY_TOURS_COLLECTION_ID', 'default_collection')
        elif "Colorado" in tour_name or "Durango" in tour_name:
            return os.getenv('OUTLINE_COLORADO_COLLECTION_ID', 'default_collection')
        elif "Arizona" in tour_name:
            return os.getenv('OUTLINE_ARIZONA_COLLECTION_ID', 'default_collection')
        elif "Rental" in tour_name or "Service" in tour_name:
            return os.getenv('OUTLINE_RENTALS_COLLECTION_ID', 'default_collection')
        else:
            return os.getenv('OUTLINE_UTAH_COLLECTION_ID', 'default_collection')
    
    def extract_description_from_markdown(self, markdown_text):
        """Extract description from markdown content"""
        desc_match = re.search(r'\*\*Long Description:\*\*\s*> (.+?)(?=\n\n|\n##|\Z)', 
                              markdown_text, re.DOTALL)
        if desc_match:
            desc = desc_match.group(1).strip()
            desc = re.sub(r'>\s*', '', desc)
            return desc[:1500]
        return ""
    
    def extract_subtitle_from_markdown(self, markdown_text):
        """Extract subtitle from markdown content"""
        subtitle_match = re.search(r'\*\*Subtitle:\*\*\s*(.+?)(?=\s*\*\*|\n)', markdown_text)
        if subtitle_match:
            return subtitle_match.group(1).strip()
        return ""

if __name__ == "__main__":
    sync_system = RimToursDataSync()
    sync_system.daily_sync()
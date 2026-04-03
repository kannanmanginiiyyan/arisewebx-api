import requests
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

class AriseWebXScraper:
    """Complete data scraper for AriseWebX - extracts everything"""
    
    def __init__(self):
        self.data = {
            "scraped_at": datetime.now().isoformat(),
            "url": "",
            "status": None,
            "business_info": {},
            "social_media_links": {},
            "contact_info": {},
            "services": [],
            "pages": {},
            "portfolio": [],
            "json_ld_data": [],
            "all_links": [],
            "images": [],
            "emails": [],
            "phones": [],
            "addresses": [],
            "hidden_data": {},
            "javascript_data": {},
            "meta_tags": {},
            "headings": {},
            "text_content": {}
        }
        
    def scrape(self, url: str) -> dict:
        """Main method to scrape all data from URL"""
        print(f"Scraping: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            self.data["url"] = url
            self.data["status"] = response.status_code
            
            if response.status_code != 200:
                self.data["error"] = f"HTTP {response.status_code}"
                return self.data
            
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract everything
            self._extract_meta_tags(soup)
            self._extract_json_ld(soup)
            self._extract_social_links(soup, url)
            self._extract_contact_info(soup)
            self._extract_services(soup)
            self._extract_all_links(soup, url)
            self._extract_images(soup, url)
            self._extract_headings(soup)
            self._extract_text_content(soup)
            self._extract_hidden_elements(soup)
            self._extract_javascript_data(html)
            self._extract_business_info(soup)
            
            print(f"✓ Successfully scraped {url}")
            return self.data
            
        except Exception as e:
            self.data["error"] = str(e)
            return self.data
    
    def _extract_meta_tags(self, soup):
        """Extract all meta tags"""
        meta_data = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            if name:
                meta_data[name] = meta.get('content', '')
        self.data["meta_tags"] = meta_data
    
    def _extract_json_ld(self, soup):
        """Extract JSON-LD structured data"""
        json_ld_list = []
        for script in soup.find_all('script', type='application/ld+json'):
            if script.string:
                try:
                    json_ld_list.append(json.loads(script.string))
                except:
                    pass
        self.data["json_ld_data"] = json_ld_list
    
    def _extract_social_links(self, soup, base_url):
        """Extract all social media links"""
        social_patterns = {
            'instagram': r'(instagram\.com|instagr\.am)/[a-zA-Z0-9_\.]+',
            'linkedin': r'linkedin\.com/(company|in)/[a-zA-Z0-9\-_]+',
            'twitter': r'(twitter\.com|x\.com)/[a-zA-Z0-9_]+',
            'facebook': r'facebook\.com/[a-zA-Z0-9\.]+',
            'github': r'github\.com/[a-zA-Z0-9\-_]+',
            'youtube': r'youtube\.com/(c|channel|user)/[a-zA-Z0-9\-_]+',
            'tiktok': r'tiktok\.com/@[a-zA-Z0-9_\.]+',
            'pinterest': r'pinterest\.com/[a-zA-Z0-9_\.]+'
        }
        
        social_links = {}
        for platform, pattern in social_patterns.items():
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                if re.search(pattern, full_url, re.IGNORECASE):
                    social_links[platform] = full_url
                    break
        
        self.data["social_media_links"] = social_links
    
    def _extract_contact_info(self, soup):
        """Extract emails, phones, addresses"""
        html_text = str(soup)
        
        # Emails
        emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_text)))
        self.data["emails"] = emails
        
        # Phones
        phones = list(set(re.findall(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', html_text)))
        phones = [re.sub(r'[^\d\+]', '', p) for p in phones if len(re.sub(r'[^\d\+]', '', p)) >= 10]
        self.data["phones"] = phones
        
        # Addresses
        address_pattern = r'\d{1,5}\s\w+(?:\s\w+){1,5},\s\w+(?:\s\w+){0,3},\s[A-Z]{2}\s\d{5}'
        addresses = list(set(re.findall(address_pattern, html_text)))
        self.data["addresses"] = addresses
    
    def _extract_services(self, soup):
        """Extract services from common patterns"""
        services = []
        
        # Look for service sections
        service_keywords = ['service', 'offer', 'provide', 'solution', 'expertise']
        for keyword in service_keywords:
            for element in soup.find_all(class_=re.compile(keyword, re.I)):
                text = element.get_text(strip=True)
                if text and len(text) < 200 and len(text) > 5:
                    services.append(text)
            
            for element in soup.find_all(id=re.compile(keyword, re.I)):
                text = element.get_text(strip=True)
                if text and len(text) < 200 and len(text) > 5:
                    services.append(text)
        
        # Remove duplicates and limit
        self.data["services"] = list(dict.fromkeys(services))[:20]
    
    def _extract_all_links(self, soup, base_url):
        """Extract all unique links"""
        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                full_url = urljoin(base_url, href)
                links.add(full_url)
        
        self.data["all_links"] = list(links)[:100]  # Limit to 100
    
    def _extract_images(self, soup, base_url):
        """Extract all image URLs"""
        images = []
        for img in soup.find_all('img', src=True):
            src = img['src']
            full_url = urljoin(base_url, src)
            alt = img.get('alt', '')
            images.append({"url": full_url, "alt": alt})
        
        self.data["images"] = images[:50]  # Limit to 50
    
    def _extract_headings(self, soup):
        """Extract all headings (H1, H2, H3)"""
        headings = {
            "h1": [h.get_text(strip=True) for h in soup.find_all('h1')],
            "h2": [h.get_text(strip=True) for h in soup.find_all('h2')],
            "h3": [h.get_text(strip=True) for h in soup.find_all('h3')]
        }
        self.data["headings"] = headings
    
    def _extract_text_content(self, soup):
        """Extract main text content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        self.data["text_content"] = {
            "full_text": text[:5000],  # First 5000 chars
            "length": len(text)
        }
    
    def _extract_hidden_elements(self, soup):
        """Extract hidden elements and data attributes"""
        hidden = {
            "hidden_elements": [],
            "data_attributes": [],
            "comments": []
        }
        
        # Hidden elements
        for element in soup.select('[style*="display: none"], [style*="visibility: hidden"], [hidden]'):
            hidden["hidden_elements"].append({
                "tag": element.name,
                "text": element.get_text(strip=True)[:300],
                "id": element.get('id', ''),
                "class": ' '.join(element.get('class', []))
            })
        
        # Data attributes
        for element in soup.find_all(attrs={"data-": re.compile(r".*")}):
            attrs = {k: v for k, v in element.attrs.items() if k.startswith('data-')}
            if attrs:
                hidden["data_attributes"].append({
                    "tag": element.name,
                    "attributes": attrs
                })
        
        # Comments
        comments = []
        for comment in soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in text):
            comments.append(comment.strip())
        hidden["comments"] = comments[:20]
        
        self.data["hidden_data"] = hidden
    
    def _extract_javascript_data(self, html):
        """Extract data from JavaScript variables"""
        js_data = {}
        
        patterns = {
            '__NEXT_DATA__': r'__NEXT_DATA__\s*=\s*({.*?});',
            '__NUXT__': r'__NUXT__\s*=\s*({.*?});',
            '__INITIAL_STATE__': r'__INITIAL_STATE__\s*=\s*({.*?});',
            'window\.__DATA__': r'window\.__DATA__\s*=\s*({.*?});'
        }
        
        for name, pattern in patterns.items():
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    js_data[name] = json.loads(match.group(1))
                except:
                    js_data[name] = match.group(1)[:500]
        
        self.data["javascript_data"] = js_data
    
    def _extract_business_info(self, soup):
        """Extract business information"""
        biz_info = {}
        
        # Look for business name
        title = soup.find('title')
        if title:
            biz_info["site_title"] = title.get_text(strip=True)
        
        # Description from meta
        desc = soup.find('meta', attrs={'name': 'description'})
        if desc:
            biz_info["description"] = desc.get('content', '')
        
        # From JSON-LD
        for ld in self.data["json_ld_data"]:
            if isinstance(ld, dict):
                if ld.get('name'):
                    biz_info["name"] = ld.get('name')
                if ld.get('priceRange'):
                    biz_info["price_range"] = ld.get('priceRange')
        
        self.data["business_info"] = biz_info

def main():
    """Run the scraper"""
    print("=" * 60)
    print("AriseWebX Complete Data Scraper")
    print("=" * 60)
    
    # Create scraper instance
    scraper = AriseWebXScraper()
    
    # URLs to try
    urls = [
        "https://www.arisewebx.com",
        "https://arisewebx.vercel.app"
    ]
    
    all_results = {}
    
    for url in urls:
        print(f"\n📡 Scraping {url}...")
        result = scraper.scrape(url)
        
        if "error" not in result:
            all_results[url] = result
            print(f"✅ Success! Data extracted:")
            print(f"   - Social links: {len(result['social_media_links'])} found")
            print(f"   - Emails: {len(result['emails'])} found")
            print(f"   - Services: {len(result['services'])} found")
            print(f"   - Images: {len(result['images'])} found")
            print(f"   - Links: {len(result['all_links'])} found")
        else:
            print(f"❌ Failed: {result['error']}")
    
    # Save results
    if all_results:
        output_file = "arisewebx_scraped_data.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n" + "=" * 60)
        print(f"✅ DATA SAVED TO: {output_file}")
        print("=" * 60)
        
        # Print summary of what was found
        for url, data in all_results.items():
            print(f"\n📊 SUMMARY for {url}:")
            print(f"   Instagram: {data['social_media_links'].get('instagram', 'Not found')}")
            print(f"   LinkedIn: {data['social_media_links'].get('linkedin', 'Not found')}")
            print(f"   Twitter: {data['social_media_links'].get('twitter', 'Not found')}")
            print(f"   Email: {', '.join(data['emails']) if data['emails'] else 'Not found'}")
            print(f"   Phone: {', '.join(data['phones']) if data['phones'] else 'Not found'}")
    else:
        print("\n❌ No data could be extracted. Website is currently broken.")

if __name__ == "__main__":
    main()
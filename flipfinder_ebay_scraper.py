import re
import urllib.parse
import urllib.request
import ssl
import time
import random
from bs4 import BeautifulSoup

def get_sold_listings_for_flipfinder(query, max_retries=2):
    """
    Get UP TO 10 most recent sold listings from eBay US for FlipFinder analysis
    Uses the original EbayScraper approach but adapted for FlipFinder with retry logic
    """
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                # Exponential backoff for retries
                retry_delay = 5 * (2 ** (attempt - 1))  # 5s, 10s, 20s...
                print(f"Retry attempt {attempt} after {retry_delay} seconds...")
                time.sleep(retry_delay)
            
            print(f"=== SCRAPER ATTEMPT {attempt + 1} ===")
            print(f"Searching eBay for sold listings: {query}")
            
            # Use the original __GetHTML function approach
            soup = __GetHTML(query, country='us', condition='all', type='all', alreadySold=True)
            
            if not soup:
                if attempt < max_retries:
                    print(f"Failed to fetch eBay data, retrying... (attempt {attempt + 1}/{max_retries + 1})")
                    continue
                else:
                    return {
                        'success': False,
                        'error': 'eBay temporarily unavailable - please try again in a few moments',
                        'items': [],
                        'total': 0,
                        'average_price': 0
                    }
            
            # Use the original __ParseItems function approach
            all_sold_items = __ParseItems(soup)
            
            if not all_sold_items:
                if attempt < max_retries:
                    print(f"No items found, retrying... (attempt {attempt + 1}/{max_retries + 1})")
                    continue
                else:
                    return {
                        'success': False,
                        'error': f'No recent sold listings found for "{query}" on eBay. Try a different search term or check the spelling.',
                        'items': [],
                        'total': 0,
                        'average_price': 0
                    }
            
            # CRITICAL FIX: Get UP TO 10 most recent sold items for Grok filtering
            recent_items = all_sold_items[:10]  # CHANGED FROM [:3] TO [:10]
            
            print(f"✅ SCRAPER SUCCESS: Found {len(all_sold_items)} total items, returning {len(recent_items)} for filtering")
            print(f"Items being returned to extension:")
            for i, item in enumerate(recent_items):
                print(f"  {i+1}. {item['title']} - ${item['price']['value']}")
            
            return {
                'success': True,
                'items': recent_items,  # Return UP TO 10 items for Grok filtering
                'total': len(recent_items),
                'average_price': 0,  # Will be calculated after Grok filtering in extension
                'note': f'Found {len(recent_items)} eBay sold listings (ready for AI filtering)'
            }
            
        except Exception as e:
            print(f"Error in attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries:
                print(f"Retrying due to error... (attempt {attempt + 1}/{max_retries + 1})")
                continue
            else:
                return {
                    'success': False,
                    'error': f'eBay search temporarily unavailable. Please try again in a moment.',
                    'items': [],
                    'total': 0,
                    'average_price': 0
                }

# Original functions adapted from the GitHub project
def __GetHTML(query, country='us', condition='all', type='all', alreadySold=True):
    """Original GetHTML function from the GitHub project with minimal anti-detection"""
    
    countryDict = {
        'us': '.com',
        'au': '.com.au',
        'ca': '.ca',
        'uk': '.co.uk',
        'de': '.de',
        'fr': '.fr'
    }
    
    conditionDict = {
        'all': '',
        'new': '&LH_ItemCondition=1000',
        'opened': '&LH_ItemCondition=1500',
        'refurbished': '&LH_ItemCondition=2500',
        'used': '&LH_ItemCondition=3000'
    }
    
    typeDict = {
        'all': '&LH_All=1',
        'auction': '&LH_Auction=1',
        'bin': '&LH_BIN=1',
        'offers': '&LH_BO=1'
    }
    
    alreadySoldString = '&LH_Complete=1&LH_Sold=1' if alreadySold else ''
    
    # Build the URL exactly like the original
    parsedQuery = urllib.parse.quote(query).replace('%20', '+')
    url = f'https://www.ebay{countryDict[country]}/sch/i.html?_from=R40&_nkw={parsedQuery}{alreadySoldString}{conditionDict[condition]}{typeDict[type]}'
    
    print(f"Fetching eBay URL: {url}")
    
    try:
        # Create SSL context to handle certificate issues
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Use original working headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        request = urllib.request.Request(url, headers=headers)
        
        # REMOVED: No more delay - let's go fast!
        # delay = random.uniform(3.0, 5.0)
        # time.sleep(delay)
        
        response = urllib.request.urlopen(request, context=ssl_context, timeout=30)
        html_content = response.read()
        
        # Handle encoding
        try:
            html_content = html_content.decode('utf-8')
        except:
            html_content = html_content.decode('utf-8', errors='ignore')
        
        print(f"Successfully fetched {len(html_content)} characters")
        
        # Check for blocking but don't fail completely
        if len(html_content) < 10000:
            print(f"⚠️ Warning: Short response ({len(html_content)} chars) - possible rate limiting")
        
        # Save debug file
        with open('debug_ebay_original.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("Saved HTML to debug_ebay_original.html")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup
        
    except Exception as e:
        print(f"Error in __GetHTML: {str(e)}")
        return None

def __ParseItems(soup):
    """Completely rewritten ParseItems function with proper syntax"""
    try:
        print("Starting item parsing...")
        
        # Try multiple selectors with proper syntax
        rawItems = []
        
        # Method 1: Try class attribute with string
        try:
            rawItems = soup.find_all('div', class_='s-item__info clearfix')
            print(f"Method 1: Found {len(rawItems)} items with class string")
        except Exception as e:
            print(f"Method 1 failed: {e}")
        
        # Method 2: Try CSS selector
        if not rawItems:
            try:
                rawItems = soup.select('div.s-item__info.clearfix')
                print(f"Method 2: Found {len(rawItems)} items with CSS selector")
            except Exception as e:
                print(f"Method 2 failed: {e}")
        
        # Method 3: Try broader selector
        if not rawItems:
            try:
                rawItems = soup.select('.s-item__info')
                print(f"Method 3: Found {len(rawItems)} items with broad selector")
            except Exception as e:
                print(f"Method 3 failed: {e}")
        
        # Method 4: Try item wrapper
        if not rawItems:
            try:
                rawItems = soup.select('.s-item__wrapper')
                print(f"Method 4: Found {len(rawItems)} items with wrapper selector")
            except Exception as e:
                print(f"Method 4 failed: {e}")
        
        # Method 5: Last resort
        if not rawItems:
            try:
                rawItems = soup.select('.s-item')
                print(f"Method 5: Found {len(rawItems)} items with simple selector")
            except Exception as e:
                print(f"Method 5 failed: {e}")
        
        if not rawItems:
            print("No items found with any selector method")
            return []
        
        data = []
        
        # Parse items - skip first item (usually ad)
        items_to_process = rawItems[1:] if len(rawItems) > 1 else rawItems
        
        for i, item in enumerate(items_to_process):
            try:
                # Get title
                title = None
                title_elem = item.find(class_='s-item__title')
                if title_elem:
                    title_span = title_elem.find('span')
                    if title_span:
                        title = title_span.get_text(strip=True)
                    else:
                        title = title_elem.get_text(strip=True)
                
                if not title or 'shop on ebay' in title.lower():
                    continue
                
                # Get price
                price = None
                price_elem = item.find('span', class_='s-item__price')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = parsePrice(price_text)
                
                if not price or price <= 0:
                    continue
                
                # Get URL
                url = ''
                url_elem = item.find('a')
                if url_elem and url_elem.get('href'):
                    url = url_elem.get('href')
                    if '?' in url:
                        url = url.split('?')[0]
                
                # Create item data
                itemData = {
                    'title': title,
                    'price': {
                        'value': price,
                        'currency': 'USD'
                    },
                    'condition': 'Not specified',
                    'itemWebUrl': url,
                    'soldDate': ''
                }
                
                data.append(itemData)
                print(f"Parsed item {len(data)}: {title} - ${price}")
                
                # Stop after getting 15 items
                if len(data) >= 15:
                    break
                    
            except Exception as e:
                print(f"Error parsing item {i}: {str(e)}")
                continue
        
        print(f"Successfully parsed {len(data)} items")
        return data
        
    except Exception as e:
        print(f"Error in __ParseItems: {str(e)}")
        return []

def parsePrice(priceString):
    """Enhanced price parsing function"""
    try:
        if not priceString:
            return None
        
        # Clean the string
        cleaned = priceString.replace('$', '').replace('USD', '').replace('AU$', '').replace('CA$', '').strip()
        
        # Handle comma-separated numbers
        if ',' in cleaned:
            cleaned = cleaned.replace(',', '')
        
        # Extract price with regex
        match = re.search(r'(\d+\.?\d*)', cleaned)
        if match:
            price = float(match.group(1))
            if 0 < price < 1000000:  # Sanity check
                return price
        
        return None
        
    except Exception as e:
        print(f"Price parsing error for '{priceString}': {e}")
        return None

# Test function
if __name__ == "__main__":
    print("Testing enhanced scraper...")
    result = get_sold_listings_for_flipfinder("iPhone 12")
    
    print("\n=== TEST RESULTS ===")
    print(f"Success: {result['success']}")
    print(f"Total items: {result['total']}")
    
    if result['success'] and result['items']:
        print(f"\nItems returned:")
        for i, item in enumerate(result['items']):
            print(f"  {i+1}. {item['title']} - ${item['price']['value']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
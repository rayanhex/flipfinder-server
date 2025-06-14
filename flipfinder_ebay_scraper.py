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
    """Original ParseItems function adapted from GitHub project - ENHANCED TO GET MORE ITEMS"""
    try:
        # Use the original selector from the GitHub project
        rawItems = soup.find_all('div', {'class': 's-item__info clearfix'})
        
        print(f"Found {len(rawItems)} items with original selector")
        
        # If original selector doesn't work, try alternative
        if not rawItems:
            rawItems = soup.find_all('div', class_=re.compile('s-item__info'))
            print(f"Found {len(rawItems)} items with alternative selector")
        
        if not rawItems:
            # Try even more selectors
            for selector in ['div.s-item__wrapper', 'div.s-item', '.srp-results .s-item']:
                rawItems = soup.select(selector)
                if rawItems:
                    print(f"Found {len(rawItems)} items with selector: {selector}")
                    break
        
        if not rawItems:
            print("No items found with any selector")
            return []
        
        data = []
        
        # Parse items using original approach but skip first item (usually ad)
        # ENHANCED: Try to get more items (up to 15 to ensure we get 10 good ones)
        for item in rawItems[1:]:  # Skip first item (usually ad)
            try:
                # Get item data using original approach
                title_elem = item.find(class_="s-item__title")
                if not title_elem:
                    continue
                    
                title_span = title_elem.find('span')
                title = title_span.get_text(strip=True) if title_span else title_elem.get_text(strip=True)
                
                # Skip ads and non-products
                if not title or 'shop on ebay' in title.lower():
                    continue
                
                # Get price using original approach
                price_elem = item.find('span', {'class': 's-item__price'})
                if not price_elem:
                    continue
                    
                price_text = price_elem.get_text(strip=True)
                price = __ParseRawPrice(price_text)
                
                if not price or price <= 0:
                    continue
                
                # Get shipping (optional)
                try:
                    shipping_elem = item.find('span', {'class': 's-item__shipping s-item__logisticsCost'})
                    if shipping_elem:
                        shipping_span = shipping_elem.find('span', {'class': 'ITALIC'})
                        shipping = __ParseRawPrice(shipping_span.get_text(strip=True)) if shipping_span else 0
                    else:
                        shipping = 0
                except:
                    shipping = 0
                
                # Get URL
                url_elem = item.find('a')
                url = url_elem['href'] if url_elem else ''
                
                # Clean URL
                if '?' in url:
                    url = url.split('?')[0]
                
                # Create item data in FlipFinder format
                itemData = {
                    'title': title,
                    'price': {
                        'value': price,
                        'currency': 'USD'
                    },
                    'condition': 'Not specified',  # Could be enhanced
                    'itemWebUrl': url,
                    'soldDate': ''
                }
                
                data.append(itemData)
                print(f"Successfully parsed: {title} - ${price}")
                
                # ENHANCED: Stop after getting 15 items (so we have enough to return 10)
                if len(data) >= 15:
                    break
                    
            except Exception as e:
                print(f"Error parsing individual item: {str(e)}")
                continue
        
        print(f"Final parsed items count: {len(data)}")
        return data
        
    except Exception as e:
        print(f"Error in __ParseItems: {str(e)}")
        return []

def __ParseRawPrice(string):
    """Original ParseRawPrice function from GitHub project"""
    try:
        parsedPrice = re.search(r'(\d+(?:\.\d+)?)', string.replace(',', '.'))
        if parsedPrice:
            return float(parsedPrice.group())
        else:
            return None
    except:
        return None

# Test function
if __name__ == "__main__":
    print("Testing with ENHANCED 10-item approach...")
    result = get_sold_listings_for_flipfinder("iPhone 12")
    
    print("\n=== TEST RESULTS ===")
    print(f"Success: {result['success']}")
    print(f"Total items: {result['total']}")
    print(f"Average price: ${result['average_price']}")
    
    if result['success'] and result['items']:
        print(f"\nItems returned:")
        for i, item in enumerate(result['items']):
            print(f"  {i+1}. {item['title']} - ${item['price']['value']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
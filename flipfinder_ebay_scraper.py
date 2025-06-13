import re
import urllib.parse
import urllib.request
import ssl
import time
from bs4 import BeautifulSoup

def get_sold_listings_for_flipfinder(query):
    """
    Get the 3 most recent sold listings from eBay US for FlipFinder analysis
    Uses the original EbayScraper approach but adapted for FlipFinder
    """
    try:
        print(f"Searching eBay for sold listings: {query}")
        
        # Use the original __GetHTML function approach
        soup = __GetHTML(query, country='us', condition='all', type='all', alreadySold=True)
        
        if not soup:
            return {
                'success': False,
                'error': 'Failed to fetch eBay data',
                'items': [],
                'total': 0
            }
        
        # Use the original __ParseItems function approach
        all_sold_items = __ParseItems(soup)
        
        if not all_sold_items:
            return {
                'success': False,
                'error': 'No sold listings found for this search term',
                'items': [],
                'total': 0
            }
        
        # Get the 3 most recent sold items
        recent_items = all_sold_items[:3]
        
        print(f"Found {len(recent_items)} recent sold items")
        
        return {
            'success': True,
            'items': recent_items,
            'total': len(recent_items),
            'note': 'Based on actual sold listings from eBay'
        }
        
    except Exception as e:
        print(f"Error in get_sold_listings_for_flipfinder: {str(e)}")
        return {
            'success': False,
            'error': f'Scraping error: {str(e)}',
            'items': [],
            'total': 0
        }

# Original functions adapted from the GitHub project
def __GetHTML(query, country='us', condition='all', type='all', alreadySold=True):
    """Original GetHTML function from the GitHub project"""
    
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
    
    print(f"Using original URL format: {url}")
    
    try:
        # Create SSL context to handle certificate issues
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Use original headers approach but add SSL context
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        request = urllib.request.Request(url, headers=headers)
        
        # Add delay to avoid being blocked
        time.sleep(2)
        
        response = urllib.request.urlopen(request, context=ssl_context, timeout=30)
        html_content = response.read()
        
        # Handle encoding
        try:
            html_content = html_content.decode('utf-8')
        except:
            html_content = html_content.decode('utf-8', errors='ignore')
        
        print(f"Successfully fetched {len(html_content)} characters")
        
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
    """Original ParseItems function adapted from GitHub project"""
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
        for item in rawItems[1:]:
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
                
                # Stop after getting enough items
                if len(data) >= 10:
                    break
                    
            except Exception as e:
                print(f"Error parsing individual item: {str(e)}")
                continue
        
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
    print("Testing with ORIGINAL GitHub approach...")
    result = get_sold_listings_for_flipfinder("iPhone 12")
    
    print("\n=== TEST RESULTS ===")
    print(f"Success: {result['success']}")
    print(f"Total items: {result['total']}")
    
    if result['success'] and result['items']:
        print(f"\nFirst item:")
        item = result['items'][0]
        print(f"Title: {item['title']}")
        print(f"Price: ${item['price']['value']}")
        print(f"URL: {item['itemWebUrl']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
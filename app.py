from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from flipfinder_ebay_scraper import get_sold_listings_for_flipfinder

app = Flask(__name__)
CORS(app)  # Enable CORS for Chrome extension

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'FlipFinder eBay Scraper API is running',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/sold-listings': 'Get sold listings for FlipFinder analysis',
            'GET /api/test': 'Test the scraper with iPhone search'
        }
    })

@app.route('/api/sold-listings', methods=['POST'])
def get_sold_listings():
    """
    Get sold listings for FlipFinder Chrome extension
    Expected input: { "query": "product name" }
    Returns: { "items": [...], "total": 3, "note": "..." }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data or 'query' not in data:
            print("ERROR: Missing query parameter")
            return jsonify({
                'success': False,
                'error': 'Missing query parameter',
                'items': [],
                'total': 0
            }), 400
            
        query = data['query'].strip()
        if not query:
            print("ERROR: Empty query provided")
            return jsonify({
                'success': False,
                'error': 'Empty query provided',
                'items': [],
                'total': 0
            }), 400
            
        print(f"=== FLASK API REQUEST ===")
        print(f"Searching eBay for: {query}")
        
        # Get sold listings using our scraper
        result = get_sold_listings_for_flipfinder(query)
        
        print(f"=== SCRAPER RESULT ===")
        print(f"Success: {result['success']}")
        print(f"Total items: {result['total']}")
        print(f"Error (if any): {result.get('error', 'None')}")
        
        if result['success']:
            # Use the average price calculated by the scraper
            average_price = result.get('average_price', 0)
            print(f"Found {result['total']} sold listings, average price: ${average_price:.2f}")
            
            # Return in the exact format expected by FlipFinder extension
            response_data = {
                'items': result['items'],
                'total': result['total'],
                'note': result['note'],
                'average_price': average_price  # Include average price for potential future use
            }
            
            print(f"=== FLASK API RESPONSE ===")
            print(f"Returning {len(result['items'])} items to extension")
            
            return jsonify(response_data)
            
        else:
            print(f"=== SCRAPER ERROR ===")
            print(f"Error: {result['error']}")
            return jsonify({
                'error': result['error'],
                'items': [],
                'total': 0
            }), 404
            
    except Exception as e:
        print(f"=== FLASK SERVER ERROR ===")
        print(f"Server error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        return jsonify({
            'error': f'Server error: {str(e)}',
            'items': [],
            'total': 0
        }), 500

@app.route('/api/test', methods=['GET'])
def test_scraper():
    """Test endpoint to verify scraper is working"""
    try:
        print("=== TESTING SCRAPER ===")
        # Test with a common product
        result = get_sold_listings_for_flipfinder("iPhone")
        
        # Calculate average price if items exist
        average_price = result.get('average_price', 0)
        if not average_price and result['success'] and result['items']:
            prices = [item['price']['value'] for item in result['items']]
            average_price = sum(prices) / len(prices)
        
        test_response = {
            'test_query': 'iPhone',
            'success': result['success'],
            'total_found': result['total'],
            'average_price': round(average_price, 2),
            'sample_item': result['items'][0] if result['items'] else None,
            'error': result.get('error', None)
        }
        
        print(f"Test result: {test_response}")
        return jsonify(test_response)
        
    except Exception as e:
        print(f"Test error: {str(e)}")
        return jsonify({
            'test_query': 'iPhone',
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'FlipFinder scraper is running'
    })

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting FlipFinder scraper server on port {port}")
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=False)
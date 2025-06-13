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
            'POST /api/sold-listings': 'Get sold listings for FlipFinder analysis'
        }
    })

@app.route('/api/sold-listings', methods=['POST'])
def get_sold_listings():
    """
    Get sold listings for FlipFinder Chrome extension
    Expected input: { "query": "product name" }
    Returns: { "items": [...], "total": 3, "average_price": 123.45 }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing query parameter',
                'items': [],
                'total': 0
            }), 400
        
        query = data['query'].strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Empty query provided',
                'items': [],
                'total': 0
            }), 400
        
        print(f"Searching eBay for: {query}")
        
        # Get sold listings using our scraper
        result = get_sold_listings_for_flipfinder(query)
        
        if result['success']:
            print(f"Found {result['total']} sold listings, average price: ${result['average_price']}")
            
            # Return in the exact format expected by FlipFinder extension
            return jsonify({
                'items': result['items'],
                'total': result['total'],
                'note': result['note']
            })
        else:
            print(f"Error: {result['error']}")
            return jsonify({
                'error': result['error'],
                'items': [],
                'total': 0
            }), 404
            
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}',
            'items': [],
            'total': 0
        }), 500

@app.route('/api/test', methods=['GET'])
def test_scraper():
    """Test endpoint to verify scraper is working"""
    try:
        # Test with a common product
        result = get_sold_listings_for_flipfinder("iPhone")
        
        return jsonify({
            'test_query': 'iPhone',
            'success': result['success'],
            'total_found': result['total'],
            'average_price': result.get('average_price', 0),
            'sample_item': result['items'][0] if result['items'] else None
        })
        
    except Exception as e:
        return jsonify({
            'test_query': 'iPhone',
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=False)
import os
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory

from feed.feed_generator import FeedGenerator

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")


@app.route('/')
def index():
    """Render the main page with the reel feed."""
    return render_template('index.html')


@app.route('/videos/<filename>')
def serve_video(filename):
    """Serve video files from the data/reels directory."""
    video_dir = os.path.join(os.path.dirname(__file__), 'data', 'reels')
    
    # Security: Only allow video files
    if not filename.endswith(('.mp4', '.webm', '.mov', '.avi')):
        return jsonify({"error": "Invalid file type"}), 400
    
    response = send_from_directory(video_dir, filename)
    
    # Set headers for video streaming
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Cache-Control'] = 'public, max-age=3600'
    
    return response


@app.route('/api/feed', methods=['GET'])
def get_feed():
    """
    API endpoint to get the reel feed for e-commerce.
    
    Query Parameters:
        user_id (optional): User ID for personalized feed
        
    Returns:
    {
        "success": true,
        "reels": [
            {
                "id": "reel1",
                "shortDescription": "Reel description",
                "longDescription": "Full description",
                "products": [...],
                "hashtags": [...],
                "url": "video_url",
                "influencer": {...}
            }
        ]
    }
    """
    try:
        user_id = request.args.get('user_id')
        
        feed_generator = FeedGenerator()
        generated_feed = feed_generator.generate_feed(user_profile={'user_id': user_id} if user_id else None)
        
        # Convert Reel objects to dictionaries
        feed_data = []
        for reel in generated_feed:
            reel_dict = {
                'id': reel.id,
                'shortDescription': reel.shortDescription,
                'longDescription': reel.longDescription,
                'products': reel.products,
                'hashtags': reel.hashtags,
                'url': reel.url,
                'influencer': reel.influencer
            }
            feed_data.append(reel_dict)
        
        return jsonify({
            "success": True,
            "reels": feed_data
        })

    except Exception as e:
        logger.error(f"Error in get_feed endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}"
        }), 500


@app.route('/api/reel/<reel_id>', methods=['GET'])
def get_reel(reel_id):
    """
    API endpoint to get a specific reel by ID.
    
    Returns:
    {
        "success": true,
        "reel": {...}
    }
    """
    try:
        feed_generator = FeedGenerator()
        feed = feed_generator.generate_feed()
        
        reel = next((r for r in feed if r.id == reel_id), None)
        
        if not reel:
            return jsonify({
                "success": False,
                "error": "Reel not found"
            }), 404
        
        reel_dict = {
            'id': reel.id,
            'shortDescription': reel.shortDescription,
            'longDescription': reel.longDescription,
            'products': reel.products,
            'hashtags': reel.hashtags,
            'url': reel.url,
            'influencer': reel.influencer
        }
        
        return jsonify({
            "success": True,
            "reel": reel_dict
        })

    except Exception as e:
        logger.error(f"Error in get_reel endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}"
        }), 500


@app.route('/api/health')
def health_check():
    """Health check endpoint to verify the API is running."""
    return jsonify({
        "status": "healthy",
        "service": "modamoments"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory

from feed.feed_generator import FeedGenerator

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")


@app.route('/')
def index():
    """Render the main page with the reel feed."""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return f"Error loading page: {str(e)}", 500


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
            try:
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
            except Exception as e:
                logger.error(f"Error processing reel: {str(e)}")
                continue
        
        return jsonify({
            "success": True,
            "reels": feed_data
        })

    except Exception as e:
        logger.error(f"Error in get_feed endpoint: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
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


@app.route('/api/influencers', methods=['GET'])
def get_influencers():
    """
    API endpoint to get all unique influencers with their details.
    
    Returns:
    {
        "success": true,
        "influencers": [
            {
                "name": "Influencer Name",
                "username": "@username",
                "avatar": "avatar_url",
                "reel_count": 5,
                "reels": [...]
            }
        ]
    }
    """
    try:
        feed_generator = FeedGenerator()
        generated_feed = feed_generator.generate_feed()
        
        # Collect unique influencers with their reels
        influencers_dict = {}
        
        for reel in generated_feed:
            try:
                influencer = reel.influencer
                if not influencer:
                    continue
                    
                # Use username as unique key, fallback to name
                key = influencer.get('username', influencer.get('name', 'unknown'))
                
                if key not in influencers_dict:
                    influencers_dict[key] = {
                        'name': influencer.get('name', 'Fashion Influencer'),
                        'username': influencer.get('username', '@fashionista'),
                        'avatar': influencer.get('avatar', 'https://ui-avatars.com/api/?name=Fashion+Influencer&background=random'),
                        'reel_count': 0,
                        'reels': []
                    }
                
                # Add reel info
                influencers_dict[key]['reel_count'] += 1
                influencers_dict[key]['reels'].append({
                    'id': reel.id,
                    'shortDescription': reel.shortDescription,
                    'url': reel.url,
                    'thumbnail': reel.url  # Could be enhanced with actual thumbnails
                })
            except Exception as e:
                logger.error(f"Error processing reel for influencers: {str(e)}")
                continue
        
        # Convert to list
        influencers_list = list(influencers_dict.values())
        
        # Sort by reel count (most active first)
        influencers_list.sort(key=lambda x: x['reel_count'], reverse=True)
        
        return jsonify({
            "success": True,
            "influencers": influencers_list
        })

    except Exception as e:
        logger.error(f"Error in get_influencers endpoint: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "influencers": [],
            "error": f"An error occurred: {str(e)}"
        }), 500


@app.route('/api/waitlist', methods=['POST'])
def add_to_waitlist():
    """
    API endpoint to add an email to the waitlist.
    
    Expected JSON input:
    {
        "email": "user@example.com"
    }
    
    Returns:
    {
        "success": true,
        "message": "Successfully added to waitlist"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                "success": False,
                "error": "Email is required"
            }), 400
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[1]:
            return jsonify({
                "success": False,
                "error": "Invalid email format"
            }), 400
        
        # Load existing waitlist
        waitlist_file = os.path.join(os.path.dirname(__file__), 'data', 'waitlist.json')
        
        if os.path.exists(waitlist_file):
            with open(waitlist_file, 'r') as f:
                waitlist_data = json.load(f)
        else:
            waitlist_data = {"emails": []}
        
        # Check if email already exists
        if email in waitlist_data.get('emails', []):
            return jsonify({
                "success": False,
                "error": "Email already registered"
            }), 400
        
        # Add email to waitlist
        waitlist_data.setdefault('emails', []).append(email)
        waitlist_data['last_updated'] = str(datetime.now().isoformat())
        
        # Save waitlist
        with open(waitlist_file, 'w') as f:
            json.dump(waitlist_data, f, indent=2)
        
        logger.info(f"Added email to waitlist: {email}")
        
        return jsonify({
            "success": True,
            "message": "Successfully added to waitlist!"
        })
        
    except Exception as e:
        logger.error(f"Error adding to waitlist: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}"
        }), 500


@app.route('/api/health')
def health_check():
    """Health check endpoint to verify the API is running."""
    try:
        # Test if we can load the feed generator
        feed_generator = FeedGenerator()
        return jsonify({
            "status": "healthy",
            "service": "modamoments",
            "reels_loaded": len(feed_generator.reel_data) if feed_generator.reel_data else 0
        })
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            "status": "degraded",
            "service": "modamoments",
            "error": str(e)
        }), 503


# Fetch videos on startup (before serving requests)
try:
    from utils.video_fetcher import fetch_videos_on_startup
    logger.info("Fetching videos from external storage...")
    video_count = fetch_videos_on_startup()
    logger.info(f"Video fetch completed. {video_count} videos available.")
except ImportError:
    logger.warning("Video fetcher module not available, skipping video fetch")
except Exception as e:
    logger.error(f"Error fetching videos: {str(e)}")
    # Continue even if video fetch fails

# Log app initialization
logger.info("ModaMoments app initialized")
logger.info(f"Static folder: {app.static_folder}")
logger.info(f"Template folder: {app.template_folder}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8888))
    logger.info(f"Starting app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

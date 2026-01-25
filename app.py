import os
import json
import logging
import csv
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for, Response
from functools import wraps

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


@app.route('/api/upload/video', methods=['POST'])
def upload_video():
    """
    API endpoint to upload a video file to Railway mounted disk.
    
    Expected form data:
        - file: Video file (multipart/form-data)
        - userId (optional): User ID who is uploading
        
    Returns:
    {
        "success": true,
        "message": "Video uploaded successfully",
        "filename": "video.mp4",
        "path": "/data/modamoments/reels/video.mp4",
        "size": 1234567
    }
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file provided. Use 'file' as the form field name."
            }), 400
        
        file = request.files['file']
        user_id = request.form.get('userId', 'unknown')
        
        # Check if file was actually selected
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
        
        # Validate file extension
        allowed_extensions = {'.mp4', '.webm', '.mov', '.avi', '.mkv'}
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({
                "success": False,
                "error": f"Invalid file type. Allowed extensions: {', '.join(allowed_extensions)}"
            }), 400
        
        # Check file size (limit to 500MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        max_size = 500 * 1024 * 1024  # 500MB
        if file_size > max_size:
            return jsonify({
                "success": False,
                "error": f"File too large. Maximum size is 500MB, got {file_size / (1024*1024):.2f}MB"
            }), 400
        
        # Determine upload directory - check multiple possible paths
        upload_paths = [
            '/data/modamoments/reels',
            '/tmp/modamoments',
            '/modamoments/data',
            '/data/reels',
            os.path.join(os.path.dirname(__file__), 'data', 'reels')
        ]
        
        upload_dir = None
        for path in upload_paths:
            if os.path.exists(path) and os.path.isdir(path):
                # Check if directory is writable
                if os.access(path, os.W_OK):
                    upload_dir = path
                    logger.info(f"Using upload directory: {upload_dir}")
                    break
        
        if upload_dir is None:
            # Try to create the primary path
            primary_path = '/data/modamoments/reels'
            try:
                os.makedirs(primary_path, exist_ok=True)
                if os.access(primary_path, os.W_OK):
                    upload_dir = primary_path
                    logger.info(f"Created and using upload directory: {upload_dir}")
                else:
                    raise PermissionError(f"Cannot write to {primary_path}")
            except (OSError, PermissionError) as e:
                logger.error(f"Failed to create upload directory {primary_path}: {str(e)}")
                # Fallback to local data/reels directory
                fallback_dir = os.path.join(os.path.dirname(__file__), 'data', 'reels')
                os.makedirs(fallback_dir, exist_ok=True)
                upload_dir = fallback_dir
                logger.warning(f"Using fallback upload directory: {upload_dir}")
        
        # Save the file
        file_path = os.path.join(upload_dir, filename)
        
        # Handle filename conflicts by appending a number
        base_name, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(file_path):
            new_filename = f"{base_name}_{counter}{ext}"
            file_path = os.path.join(upload_dir, new_filename)
            filename = new_filename
            counter += 1
        
        file.save(file_path)
        
        # Get final file size
        final_size = os.path.getsize(file_path)
        
        logger.info(f"Video uploaded successfully: {filename} by user {user_id} to {file_path} ({final_size} bytes)")
        
        return jsonify({
            "success": True,
            "message": "Video uploaded successfully",
            "filename": filename,
            "path": file_path,
            "size": final_size,
            "userId": user_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"An error occurred during upload: {str(e)}"
        }), 500


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        password = request.form.get('password', '')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')  # Default password, change in production
        
        if password == admin_password:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid password')
    
    # If already logged in, redirect to dashboard
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard to view waitlist."""
    try:
        waitlist_file = os.path.join(os.path.dirname(__file__), 'data', 'waitlist.json')
        
        if os.path.exists(waitlist_file):
            with open(waitlist_file, 'r') as f:
                waitlist_data = json.load(f)
        else:
            waitlist_data = {"emails": [], "last_updated": None}
        
        emails = waitlist_data.get('emails', [])
        last_updated = waitlist_data.get('last_updated', 'Never')
        
        return render_template('admin_dashboard.html', 
                             emails=emails, 
                             count=len(emails),
                             last_updated=last_updated)
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        return render_template('admin_dashboard.html', 
                             emails=[], 
                             count=0,
                             last_updated='Error loading data',
                             error=str(e))


@app.route('/admin/waitlist/download')
@admin_required
def download_waitlist():
    """Download waitlist as CSV."""
    try:
        waitlist_file = os.path.join(os.path.dirname(__file__), 'data', 'waitlist.json')
        
        if os.path.exists(waitlist_file):
            with open(waitlist_file, 'r') as f:
                waitlist_data = json.load(f)
        else:
            waitlist_data = {"emails": [], "last_updated": None}
        
        emails = waitlist_data.get('emails', [])
        format_type = request.args.get('format', 'csv')  # csv or json
        
        if format_type == 'json':
            # Return JSON download
            response = jsonify({
                "emails": emails,
                "count": len(emails),
                "last_updated": waitlist_data.get('last_updated', 'Never'),
                "exported_at": datetime.now().isoformat()
            })
            response.headers['Content-Disposition'] = f'attachment; filename=waitlist_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            return response
        else:
            # Return CSV download
            # Create CSV in memory
            si = io.StringIO()
            writer = csv.writer(si)
            
            # Write header
            writer.writerow(['Email', 'Count'])
            
            # Write emails with index
            for idx, email in enumerate(emails, 1):
                writer.writerow([email, idx])
            
            # Create Flask response
            output = si.getvalue()
            si.close()
            
            response = Response(
                output,
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=waitlist_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                }
            )
            return response
            
    except Exception as e:
        logger.error(f"Error downloading waitlist: {str(e)}")
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

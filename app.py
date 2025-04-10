import os
import logging
from flask import Flask, request, jsonify, render_template

from feed.feed_generator import FeedGenerator
from ranker.reel_ranker import ReelRanker

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Initialize reel ranker
reel_ranker = ReelRanker()


@app.route('/')
def index():
    """Render the main page with the input form."""
    return render_template('index.html')


@app.route('/docs')
def docs():
    """Render the API documentation page."""
    return render_template('docs.html')


@app.route('/api/rank_reels', methods=['POST'])
def rank_reels():
    """
    API endpoint to rank reels based on conversation relevance.
    
    Expected JSON input:
    {
        "query": "user question or statement",
        "conversation_history": [
            {"role": "user", "content": "previous user message"},
            {"role": "assistant", "content": "previous assistant message"}
        ],
        "reels": [
            {
                "id": "reel1",
                "title": "Reel title",
                "description": "Reel description",
                "tags": ["tag1", "tag2"],
                ...
            }
        ]
    }
    
    Returns:
    {
        "ranked_reels": [
            {
                "id": "reel1",
                "title": "Reel title",
                "description": "Reel description",
                "relevance_score": 0.92,
                ...
            }
        ],
        "success": true
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        # Extract required fields
        query = data.get('query', '')
        conversation_history = data.get('conversation_history', [])
        reels = data.get('reels', [])

        # Validate inputs
        if not query:
            return jsonify({"success": False, "error": "Query is required"}), 400

        if not reels:
            return jsonify({"success": False, "error": "No reels provided for ranking"}), 400

        # Rank the reels
        ranked_reels = reel_ranker.rank_reels(query, conversation_history, reels)

        return jsonify({
            "success": True,
            "ranked_reels": ranked_reels
        })

    except Exception as e:
        logger.error(f"Error in rank_reels endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}"
        }), 500


@app.route('/api/generate_feed', methods=['GET'])
def generate_feed():
    """
    API endpoint to get all the reels for the feed.

    Expected input:
    user_id: str

    Returns:
    {
        "ranked_reels": [
            {
                "id": "reel1",
                "shortDescription": "Reel title",
                "longDescription": "Reel description",
                "products": [],
                "hashtags": [],
                "url": ""
                "relevance_score": 0.92,
            }
        ],
        "success": true
    }
    """
    try:
        data = request.args.get('user_id')

        if not data:
            return jsonify({"success": False, "error": "No user_id provided"}), 400

        # Rank the reels
        feed_generator = FeedGenerator()
        generated_feed = feed_generator.generate_feed(user_profile=None)
        generated_feed = [feed_object.__dict__ for feed_object in generated_feed]
        return jsonify(generated_feed)

    except Exception as e:
        logger.error(f"Error in rank_reels endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}"
        }), 500


@app.route('/api/health')
def health_check():
    """Health check endpoint to verify the API is running."""
    openai_status = reel_ranker.check_openai_connection()

    if openai_status["connected"]:
        return jsonify({
            "status": "healthy",
            "openai_connection": "connected"
        })
    else:
        return jsonify({
            "status": "degraded",
            "openai_connection": "disconnected",
            "error": openai_status.get("error", "Unknown error")
        }), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)

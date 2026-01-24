# ModaMoments

A reel-based e-commerce platform driven by influencers. Shop fashion directly from video reels featuring products with integrated "Shop Now" buttons.

## Features

- 📱 **TikTok-style Reel Feed**: Swipe through fashion reels in a vertical feed
- 🛍️ **Integrated Shopping**: Shop products directly from each reel with "Shop Now" buttons
- 👥 **Influencer-Driven**: Each reel is created by fashion influencers
- 🎥 **Video Content**: Watch product showcases in engaging video format
- 💳 **Product Details**: View product information, prices, sizes, and colors
- ❤️ **Social Features**: Like and share reels

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Data**: JSON-based product catalog and reel data

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Or using Poetry:
```bash
poetry install
```

2. Set environment variables (optional):
```bash
export SESSION_SECRET="your-secret-key"
```

3. Run the application:
```bash
python app.py
```

Or:
```bash
python main.py
```

The app will be available at `http://localhost:8888`

## API Endpoints

### GET `/api/feed`
Get the reel feed for e-commerce.

**Query Parameters:**
- `user_id` (optional): User ID for personalized feed

**Response:**
```json
{
  "success": true,
  "reels": [
    {
      "id": "reel_id",
      "shortDescription": "Reel description",
      "longDescription": "Full description",
      "products": [...],
      "hashtags": [...],
      "url": "video_url",
      "influencer": {
        "name": "Influencer Name",
        "username": "@username",
        "avatar": "avatar_url"
      }
    }
  ]
}
```

### GET `/api/reel/<reel_id>`
Get a specific reel by ID.

**Response:**
```json
{
  "success": true,
  "reel": {...}
}
```

### GET `/api/health`
Health check endpoint.

## Project Structure

```
modamoments/
├── app.py                 # Main Flask application
├── main.py                # Entry point
├── data/
│   ├── reels.json        # Reel data with products
│   └── product_catalog.json
├── feed/
│   └── feed_generator.py # Feed generation logic
├── reels/
│   └── reel.py           # Reel data model
├── templates/
│   └── index.html        # Main UI template
├── static/
│   ├── css/
│   │   └── custom.css    # Styling
│   └── js/
│       └── app.js        # Frontend logic
└── README.md
```

## Usage

1. Open the app in your browser
2. Scroll through the vertical reel feed
3. Click "Shop Now" on any reel to view products
4. Browse product details, sizes, and prices
5. Click "Buy Now" to purchase (opens external link)

## Development

The app uses a simple JSON-based data structure. To add new reels:

1. Add reel data to `data/reels.json`
2. Include product information, video URL, influencer details
3. Restart the server

## License

MIT

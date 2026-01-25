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

# Video Storage Configuration (choose one):
# Option 1: Remote URL (S3, HTTP, etc.)
export VIDEO_STORAGE_URL="https://your-bucket.s3.amazonaws.com/videos/"
# or
export VIDEO_STORAGE_URL="https://example.com/videos/"

# Option 2: Local Path (external drive, network mount)
export VIDEO_STORAGE_PATH="/Volumes/ExternalDrive/videos"
# or
export VIDEO_STORAGE_PATH="/mnt/network-storage/reels"
```

**Video Storage Options:**
- **VIDEO_STORAGE_URL**: Remote URL where videos are stored (S3, CDN, HTTP server)
  - Videos will be downloaded during server startup
  - Supports S3-compatible storage and regular HTTP/HTTPS URLs
- **VIDEO_STORAGE_PATH**: Local path to videos (external drive, network mount)
  - Videos will be copied during server startup
  - Useful for external drives, NAS, or mounted volumes
- **No configuration**: Videos must be in `data/reels/` directory

3. Run the application:
```bash
python app.py
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

## Deployment on Railway

### Prerequisites
- A Railway account (sign up at [railway.app](https://railway.app))
- Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)

### Deployment Steps

1. **Create a new project on Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo" (or your Git provider)
   - Choose your repository

2. **Configure the project:**
   - Railway will automatically detect Python and use the `Procfile`
   - The app will use Gunicorn as specified in the Procfile

3. **Set Environment Variables (optional):**
   - Go to your project settings
   - Add environment variables if needed:
     - `SESSION_SECRET`: Your secret key for Flask sessions (optional)

4. **Deploy:**
   - Railway will automatically build and deploy your app
   - The app will be available at a Railway-provided URL

### Important Files for Railway

- `Procfile`: Specifies how to run the app with Gunicorn
- `railway.json`: Railway-specific configuration
- `requirements.txt`: Python dependencies
- `runtime.txt`: Python version specification

### Notes

- Railway automatically provides a `PORT` environment variable
- The app is configured to use this port automatically
- Gunicorn is used as the production server (not Flask's development server)
- Static files are served by Flask in production

### Troubleshooting

If deployment fails:
1. Check Railway logs for error messages
2. Ensure all dependencies are in `requirements.txt`
3. Verify the `Procfile` is correct
4. Check that Python version in `runtime.txt` is supported

## Downloading the App

### Option 1: Clone from Git Repository

If you have the repository on GitHub/GitLab:

```bash
git clone <repository-url>
cd modamoments
```

### Option 2: Download as ZIP

1. If the repository is on GitHub:
   - Go to the repository page
   - Click the green "Code" button
   - Select "Download ZIP"
   - Extract the ZIP file

2. If you have the files locally:
   ```bash
   # Create a ZIP file of the project
   cd /path/to/parent/directory
   zip -r modamoments.zip modamoments -x "*.pyc" -x "__pycache__" -x "*.git*"
   ```

### Option 3: Copy Files Manually

The project is located at:
```
/Users/shantanuaggarwal/Documents/yc_comb/modamoments
```

You can copy this entire directory to another location or machine.

### Option 4: Set Up Git Repository

To share via Git:

```bash
cd /Users/shantanuaggarwal/Documents/yc_comb/modamoments

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: ModaMoments app"

# Add remote repository (if you have one)
git remote add origin <your-repo-url>

# Push to remote
git push -u origin main
```

### Quick Start After Download

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   python app.py
   ```

3. **Access the app:**
   - Open browser to `http://localhost:8888`

## License

MIT

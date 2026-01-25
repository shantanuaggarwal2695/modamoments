# Railway Video Storage Setup Guide

This guide explains how to upload videos to Railway's mounted volume at `/modamoments/data`.

## Dockerfile Setup

The project now includes a `Dockerfile` that:
- Creates mount point directories (`/modamoments/data`, `/data`)
- Sets up the Python environment
- Configures the app to work with Railway's volume mounting

The `railway.json` is configured to use Dockerfile instead of Nixpacks.

## Step 1: Configure Environment Variable

In your Railway project dashboard:

1. Go to your service → **Variables**
2. Add a new environment variable:
   ```
   VIDEO_STORAGE_PATH=/modamoments/data
   ```
3. Save the changes

## Step 2: Upload Videos to Railway Volume

You have several options to upload videos:

### Option A: Using Railway CLI (Recommended)

1. **Install Railway CLI** (if not already installed):
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Link your project**:
   ```bash
   railway link
   ```

4. **Upload videos from your local machine**:
   
   **Method 1: Using Railway CLI with file transfer**
   ```bash
   # First, check if the volume is accessible
   railway run --service modamoments -- ls -la /modamoments/data
   
   # If the directory doesn't exist or is read-only, try just /data
   railway run --service modamoments -- ls -la /data
   
   # Upload videos one by one (replace with your actual local path)
   cd /Users/shantanuaggarwal/Documents/yc_comb/modamoments
   for video in data/reels/*.mp4; do
     filename=$(basename "$video")
     echo "Uploading $filename..."
     cat "$video" | railway run --service modamoments -- \
       sh -c "cat > /modamoments/data/$filename"
   done
   ```
   
   **Method 2: Using Railway's file upload (if available)**
   - Go to Railway dashboard → Your service → Volume
   - Use the file upload interface if available
   
   **Method 3: Copy from Railway's project directory**
   ```bash
   # If videos are in your Railway project's data/reels/ directory
   railway run --service modamoments -- \
     sh -c "mkdir -p /modamoments/data && cp -r data/reels/*.mp4 /modamoments/data/ 2>/dev/null || cp -r data/reels/*.mp4 /data/ 2>/dev/null || true"
   ```

### Option B: Using Railway Volume Shell

1. **Open Railway Volume Shell**:
   - Go to your Railway project
   - Click on the **Volume** tab
   - Click **Open Shell**

2. **Create directory and upload**:
   ```bash
   mkdir -p /modamoments/data
   # Then use Railway's file upload feature or SCP
   ```

### Option C: Using SCP/SFTP (if enabled)

If Railway provides SSH access:

```bash
# Get your Railway SSH connection details from the dashboard
scp -r data/reels/* railway:/data/
```

### Option D: Upload via Deployment Script

Create a deployment script that uploads videos during build:

1. **Create `scripts/upload_videos.sh`**:
   ```bash
   #!/bin/bash
   # This script runs during deployment
   
   if [ -d "data/reels" ]; then
     mkdir -p /modamoments/data
     cp -r data/reels/* /modamoments/data/ 2>/dev/null || true
   fi
   ```

2. **Update your build command** in `railway.json`:
   ```json
   {
     "build": {
       "builder": "NIXPACKS",
       "buildCommand": "pip install -r requirements.txt && bash scripts/upload_videos.sh"
     }
   }
   ```

### Option E: Download from Remote Source

Instead of uploading, configure videos to download from a remote source:

1. **Set environment variable**:
   ```
   VIDEO_STORAGE_URL=https://your-bucket.s3.amazonaws.com/videos/
   ```

2. Videos will be automatically downloaded to `/data` during startup.

## Step 3: Verify Videos Are Uploaded

After uploading, verify the videos are in the volume:

1. **Check via Railway Shell**:
   ```bash
   railway run --service your-service-name -- ls -la /modamoments/data
   ```

2. **Check via logs**:
   The app will log video fetch status on startup. Look for:
   ```
   Fetching videos from local path: /modamoments/data
   Copied: video1.mp4
   Copied: video2.mp4
   ...
   Video fetch completed. X videos available.
   ```

## Step 4: Video File Structure

Your videos should be in `/modamoments/data` with filenames matching `reels.json`:

```
/modamoments/data/
├── video1.mp4
├── video2.mp4
├── video3.mp4
├── ...
└── video27.mp4
```

The filenames must match the keys in `data/reels.json` (e.g., `video1.mp4`, `video2.mp4`, etc.).

## Troubleshooting

### Videos not found
- Check that `VIDEO_STORAGE_PATH=/modamoments/data` is set in Railway environment variables
- Verify videos exist in `/modamoments/data` using Railway shell
- Check app logs for video fetch errors

### Permission errors
- Ensure the Railway service has read access to `/modamoments/data`
- Check volume mount permissions in Railway dashboard

### Videos not copying
- Verify the source path exists: `ls -la /modamoments/data`
- Check that video filenames match `reels.json` keys exactly
- Review app startup logs for fetch errors

## Quick Upload Script

A ready-to-use script is available at `scripts/upload_videos_railway.sh`:

```bash
# Make it executable (if not already)
chmod +x scripts/upload_videos_railway.sh

# Run it
./scripts/upload_videos_railway.sh
```

Or manually, save this as `upload_to_railway.sh`:

```bash
#!/bin/bash
# Upload videos to Railway volume

SERVICE_NAME="your-service-name"  # Replace with your service name
VIDEO_DIR="data/reels"

echo "Uploading videos to Railway volume..."

# List videos to upload
videos=$(ls $VIDEO_DIR/*.mp4 2>/dev/null)
if [ -z "$videos" ]; then
  echo "No videos found in $VIDEO_DIR"
  exit 1
fi

echo "Found videos:"
ls -lh $VIDEO_DIR/*.mp4

# Upload each video
for video in $VIDEO_DIR/*.mp4; do
  filename=$(basename "$video")
  echo "Uploading $filename..."
  railway run --service $SERVICE_NAME -- \
    sh -c "mkdir -p /modamoments/data && cat > /modamoments/data/$filename" < "$video"
done

echo "Upload complete!"
```

Make it executable and run:
```bash
chmod +x upload_to_railway.sh
./upload_to_railway.sh
```

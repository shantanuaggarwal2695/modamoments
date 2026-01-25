# Railway Video Storage Setup Guide

This guide explains how to upload videos to Railway's mounted volume at `/data`.

## Step 1: Configure Environment Variable

In your Railway project dashboard:

1. Go to your service → **Variables**
2. Add a new environment variable:
   ```
   VIDEO_STORAGE_PATH=/data
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

4. **Upload videos**:
   ```bash
   # Upload all videos from local data/reels/ directory
   railway run --service your-service-name -- \
     sh -c "mkdir -p /data && cp -r data/reels/* /data/"
   
   # Or upload specific videos
   railway run --service your-service-name -- \
     sh -c "mkdir -p /data && cp video1.mp4 video2.mp4 /data/"
   ```

### Option B: Using Railway Volume Shell

1. **Open Railway Volume Shell**:
   - Go to your Railway project
   - Click on the **Volume** tab
   - Click **Open Shell**

2. **Create directory and upload**:
   ```bash
   mkdir -p /data
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
     mkdir -p /data
     cp -r data/reels/* /data/ 2>/dev/null || true
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
   railway run --service your-service-name -- ls -la /data
   ```

2. **Check via logs**:
   The app will log video fetch status on startup. Look for:
   ```
   Fetching videos from local path: /data
   Copied: video1.mp4
   Copied: video2.mp4
   ...
   Video fetch completed. X videos available.
   ```

## Step 4: Video File Structure

Your videos should be in `/data` with filenames matching `reels.json`:

```
/data/
├── video1.mp4
├── video2.mp4
├── video3.mp4
├── ...
└── video27.mp4
```

The filenames must match the keys in `data/reels.json` (e.g., `video1.mp4`, `video2.mp4`, etc.).

## Troubleshooting

### Videos not found
- Check that `VIDEO_STORAGE_PATH=/data` is set in Railway environment variables
- Verify videos exist in `/data` using Railway shell
- Check app logs for video fetch errors

### Permission errors
- Ensure the Railway service has read access to `/data`
- Check volume mount permissions in Railway dashboard

### Videos not copying
- Verify the source path exists: `ls -la /data`
- Check that video filenames match `reels.json` keys exactly
- Review app startup logs for fetch errors

## Quick Upload Script

Save this as `upload_to_railway.sh`:

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
    sh -c "mkdir -p /data && cat > /data/$filename" < "$video"
done

echo "Upload complete!"
```

Make it executable and run:
```bash
chmod +x upload_to_railway.sh
./upload_to_railway.sh
```

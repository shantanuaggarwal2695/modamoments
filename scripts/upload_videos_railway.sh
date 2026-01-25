#!/bin/bash
# Script to upload videos to Railway's mounted volume
# Usage: ./scripts/upload_videos_railway.sh

SERVICE_NAME="modamoments"
VIDEO_DIR="data/reels"
MOUNT_PATH="/modamoments/data"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Error: Railway CLI not found. Install it with: npm i -g @railway/cli"
    exit 1
fi

# Check if video directory exists
if [ ! -d "$VIDEO_DIR" ]; then
    echo "Error: Video directory not found: $VIDEO_DIR"
    exit 1
fi

# Get list of videos
videos=$(ls $VIDEO_DIR/*.mp4 2>/dev/null)
if [ -z "$videos" ]; then
    echo "No videos found in $VIDEO_DIR"
    exit 1
fi

echo "Found videos:"
ls -lh $VIDEO_DIR/*.mp4 | awk '{print $9, "(" $5 ")"}'
echo ""

# First, check if mount path exists and is writable
echo "Checking mount path: $MOUNT_PATH"
if railway run --service $SERVICE_NAME -- test -d $MOUNT_PATH 2>/dev/null; then
    echo "✓ Mount path exists: $MOUNT_PATH"
elif railway run --service $SERVICE_NAME -- test -d /data 2>/dev/null; then
    echo "⚠ $MOUNT_PATH not found, trying /data instead"
    MOUNT_PATH="/data"
else
    echo "⚠ Warning: Mount path not found. Trying to create it..."
    railway run --service $SERVICE_NAME -- mkdir -p $MOUNT_PATH 2>/dev/null || \
    railway run --service $SERVICE_NAME -- mkdir -p /data 2>/dev/null
    if [ $? -eq 0 ]; then
        if railway run --service $SERVICE_NAME -- test -d /data 2>/dev/null; then
            MOUNT_PATH="/data"
        fi
    fi
fi

echo ""
echo "Uploading videos to: $MOUNT_PATH"
echo ""

# Upload each video
uploaded=0
failed=0

for video in $VIDEO_DIR/*.mp4; do
    filename=$(basename "$video")
    filesize=$(ls -lh "$video" | awk '{print $5}')
    
    echo -n "Uploading $filename ($filesize)... "
    
    # Upload using cat to pipe file content
    if cat "$video" | railway run --service $SERVICE_NAME -- \
        sh -c "cat > $MOUNT_PATH/$filename" 2>/dev/null; then
        echo "✓ Done"
        uploaded=$((uploaded + 1))
    else
        echo "✗ Failed"
        failed=$((failed + 1))
    fi
done

echo ""
echo "Upload complete!"
echo "  ✓ Uploaded: $uploaded"
echo "  ✗ Failed: $failed"

# Verify upload
echo ""
echo "Verifying upload..."
railway run --service $SERVICE_NAME -- ls -lh $MOUNT_PATH/*.mp4 2>/dev/null | head -10

#!/bin/bash
echo "Checking service status..."
STATUS=$(railway service status)
echo "$STATUS"

if [[ "$STATUS" == *"BUILDING"* ]]; then
  echo "⚠️  Service is still BUILDING. Please wait a few minutes and try again."
  exit 1
fi

if [[ "$STATUS" == *"CRASHED"* ]]; then
  echo "⚠️  Service CRASHED. Check 'railway logs'."
  exit 1
fi

echo "🚀 Uploading database..."
cat backend/links.db | railway ssh "cat > /app/links.db"

if [ $? -eq 0 ]; then
  echo "✅ Database uploaded successfully!"
else
  echo "❌ Upload failed. Make sure the app is running."
fi

#!/bin/bash
set -e

# Variables
DOCKER_IMAGE_NAME="my-fastapi-app"

# Set the path to the directory containing the configuration files
CONFIG_DIR="./config"

# Ensure the config directory exists
mkdir -p "$CONFIG_DIR"

# Set the path to the Facebook API configuration file
FB_CONFIG_FILE="./config.json"

# Set the path to the Google Ads API configuration file
GADS_CONFIG_FILE="./google-ads.yaml"

# Check if the Facebook API configuration file exists
if [ ! -f "$FB_CONFIG_FILE" ]; then
    echo "Error: Facebook API configuration file not found at $FB_CONFIG_FILE"
    exit 1
fi

# Check if the Google Ads API configuration file exists
if [ ! -f "$GADS_CONFIG_FILE" ]; then
    echo "Warning: Google Ads API configuration file not found at $GADS_CONFIG_FILE"
    echo "Creating a template file. Please update it with your credentials."
    
    # Create a template Google Ads configuration file
    cat > "$GADS_CONFIG_FILE" << EOL
developer_token: YOUR_DEVELOPER_TOKEN_HERE
client_id: YOUR_CLIENT_ID_HERE  
client_secret: YOUR_CLIENT_SECRET_HERE
refresh_token: YOUR_REFRESH_TOKEN_HERE
login_customer_id: YOUR_LOGIN_CUSTOMER_ID
EOL
fi

# Step 1: Build Docker image
echo "Building Docker image..."
docker build -t $DOCKER_IMAGE_NAME .

# Step 2: Run Docker container locally
echo "Running Docker container locally..."
docker run -d -p 8000:8000 \
    -v "$(pwd)/config.json:/app/config.json" \
    -v "$(pwd)/google-ads.yaml:/app/google-ads.yaml" \
    --name my-fastapi-container \
    $DOCKER_IMAGE_NAME

# Optional: Display Docker container logs (uncomment if needed)
# echo "Displaying Docker container logs..."
# docker logs -f my-fastapi-container

echo "FastAPI application is now running at http://localhost:8000"

# Instructions to stop the container
echo "To stop the container, run: docker stop my-fastapi-container"
echo "To remove the container, run: docker rm my-fastapi-container"
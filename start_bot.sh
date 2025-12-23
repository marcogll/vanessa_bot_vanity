#!/bin/bash

echo "Starting Vanessa Bot..."

# Check for .env file
if [ ! -f .env ]; then
  echo "WARNING: .env file not found."
  echo "Please create one by copying .env.example and filling in your Telegram Token and Webhook URLs."
  echo "cp .env.example .env"
  # Optionally, exit or prompt user
  # exit 1
fi

echo "Choose how to start the bot:"
echo "1) Run with Docker Compose (recommended for production/development)"
echo "2) Run directly with Python (for local development/testing)"
read -p "Enter choice (1 or 2): " choice

case $choice in
  1)
    echo "Running with Docker Compose..."
    docker-compose up --build --detach
    echo "Bot started in detached mode. Use 'docker-compose logs -f' to see logs."
    ;;
  2)
    echo "Running directly with Python..."
    # Check for virtual environment and activate it if found
    if [ -d "venv" ]; then
      source venv/bin/activate
      echo "Activated virtual environment: venv"
    elif [ -d ".venv" ]; then
      source .venv/bin/activate
      echo "Activated virtual environment: .venv"
    else
      echo "No virtual environment found. Consider creating one: python3 -m venv venv"
      echo "Installing dependencies globally (not recommended without venv)..."
      pip install -r requirements.txt
    fi
    
    # Install dependencies if not already in venv
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        pip install -r requirements.txt
    fi

    echo "Executing python app/main.py..."
    python app/main.py
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac

echo "Bot startup script finished."
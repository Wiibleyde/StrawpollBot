# Use a Python 3.8 runtime as a base image
FROM python:3.8
WORKDIR /app

# Copy the requirements file and install the necessary packages
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

# Copy the source code, configuration file, and database file
COPY main.py .
COPY config.json .
COPY logs.db .

# Set environment variables for the bot to use
ENV BOT_LOGS_DIR=/app/logs
ENV BOT_DATA_DIR=/app
ENV BOT_CONFIG_FILE=/app/config.json

# Start the bot
CMD ["python", "main.py"]

# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8787

# Environment variables
ENV PORT=8787
ENV MCP_STORAGE=/app/data/usage.json

# Create data directory
RUN mkdir -p /app/data

# Run the application
CMD ["python", "mcp_server_v2.py"]

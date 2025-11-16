FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DUNE_API_KEY=""

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config/ ./config/
COPY dbt/ ./dbt/
COPY config/dbt_project.yml ./dbt_project.yml
COPY dbt/profiles.yml ./dbt/profiles.yml

# Create directories for data and logs
RUN mkdir -p data/databases data/exports data/logs dbt/target

# Make scripts executable
RUN chmod +x src/*.py scripts/*.sh

# Set default command
CMD ["python", "src/scheduler.py", "daemon"]

# 1. Use a lightweight, stable Python runtime
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install system dependencies required for compilation (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy dependency configurations first (takes advantage of Docker caching)
COPY requirements.txt .

# 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of your bot's code into the container
COPY . .

# 7. Run your bot script unbuffered so logs appear instantly in Coolify
CMD ["python", "-u", "main.py"]

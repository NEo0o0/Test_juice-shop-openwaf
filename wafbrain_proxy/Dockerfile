# Use python 3.9 slim which provides good compatibility with tensorflow/keras
FROM python:3.9-slim

WORKDIR /app

# System dependencies for compiling any C extensions needed by tensorflow/keras
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the proxy script
COPY proxy.py .

# The proxy will listen on port 80
EXPOSE 80

CMD ["python", "proxy.py"]

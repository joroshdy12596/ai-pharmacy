FROM python:3.8

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/app:${PATH}"

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    fonts-dejavu \
    udev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p media static staticfiles

# Make sure the printer device exists
RUN mkdir -p /dev/usb

# Give permissions to access USB devices
RUN chmod -R 777 /dev/usb || true

ENTRYPOINT ["/app/docker-entrypoint.sh"]
# Shell form (not exec-form array) so ${PORT} expands - Render assigns its
# own port via this env var; falls back to 8000 for local docker-compose.
CMD python manage.py runserver 0.0.0.0:${PORT:-8000}

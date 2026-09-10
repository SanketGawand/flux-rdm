FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    QT_QPA_PLATFORM=xcb \
    PYTHONPATH=/

# Install FreeRDP 3, Qt6 dependencies, X11 inspection tools, and standard fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-pyqt6 \
    python3-pyqt6.qtsvg \
    freerdp3-x11 \
    wmctrl \
    xdotool \
    libx11-dev \
    libxext-dev \
    libxrandr-dev \
    libxtst-dev \
    xterm \
    openssh-client \
    zenity \
    ca-certificates \
    fonts-dejavu-core \
    fonts-liberation \
    libgl1 \
    libglx-mesa0 \
    libegl1 \
    && rm -rf /var/lib/apt/lists/*

# Handle existing UID 1000 user and configure appuser
RUN CURRENT_USER=$(getent passwd 1000 | cut -d: -f1) && \
    if [ -n "$CURRENT_USER" ]; then userdel -r "$CURRENT_USER" 2>/dev/null || true; fi && \
    useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /home/appuser/data /home/appuser/imports /app && \
    chown -R appuser:appuser /home/appuser /app

WORKDIR /app

# Install dependencies from requirements.txt
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /app/requirements.txt

# Copy the app directory contents directly into /app
COPY app/ /app/
RUN chown -R appuser:appuser /app

USER appuser

ENTRYPOINT ["python3", "main.py"]

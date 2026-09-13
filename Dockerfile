FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    QT_QPA_PLATFORM=xcb \
    PYTHONPATH=/

# Install FreeRDP 3, Qt6 dependencies, X11 inspection tools, standard fonts, utilities, and gosu
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
    wget \
    apt-transport-https \
    software-properties-common \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install PowerShell Core (pwsh) and NTLM dependencies for WinRM
RUN wget -q "https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb" && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y powershell gss-ntlmssp && \
    rm -rf /var/lib/apt/lists/*

# Patch WSMan for Linux (fixes the "no supported WSMan client library was found" error)
RUN pwsh -NoProfile -Command "Install-Module -Name PSWSMan -Force -Scope AllUsers; Install-WSMan"

# Handle existing UID 1000 user, configure appuser, and pre-create all volume mount points
RUN CURRENT_USER=$(getent passwd 1000 | cut -d: -f1) && \
    if [ -n "$CURRENT_USER" ]; then userdel -r "$CURRENT_USER" 2>/dev/null || true; fi && \
    useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /home/appuser/data /home/appuser/imports /app /app/shared && \
    chown -R appuser:appuser /home/appuser /app

WORKDIR /app

# Install dependencies from requirements.txt
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /app/requirements.txt

# Copy the app directory contents directly into /app
COPY app/ /app/
RUN chown -R appuser:appuser /app
COPY CHANGELOG.md .

# Create self-healing entrypoint to fix permissions on ALL mapped host volumes before dropping to appuser
RUN echo '#!/bin/bash\n\
chown -R appuser:appuser /app/shared /home/appuser/data /home/appuser/imports\n\
exec gosu appuser "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Start as root (to allow chown), entrypoint handles the downgrade to appuser
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python3", "main.py"]

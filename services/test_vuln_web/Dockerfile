FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    openssh-server \
    iputils-ping \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Setup SSH
RUN mkdir -p /var/run/sshd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Install Python packages
RUN pip install flask

# Create ctf user with sudo privileges for patching (but limited)
RUN useradd -m -u 1000 -s /bin/bash ctf && \
    echo "ctf ALL=(ALL) NOPASSWD: /usr/bin/apt, /usr/bin/systemctl restart *" >> /etc/sudoers

# Create entrypoint script
RUN cat > /entrypoint.sh << 'EOF'
#!/bin/bash

# Create random user if credentials provided
if [ ! -z "$CTF_USERNAME" ]; then
# Create user
useradd -m -s /bin/bash "$CTF_USERNAME"
echo "$CTF_USERNAME:$CTF_PASSWORD" | chpasswd

# Give limited sudo for patching
echo "$CTF_USERNAME ALL=(ALL) NOPASSWD: /usr/bin/apt, /usr/bin/systemctl restart *, /bin/systemctl restart *" >> /etc/sudoers

echo "Created user: $CTF_USERNAME"
fi

# Start SSH
service ssh start

# Create flag placeholders (will be replaced by gameserver)
mkdir -p /home/ctf
echo "FLAG{test_user_flag}" > /home/ctf/flag1.txt
chown ctf:ctf /home/ctf/flag1.txt
chmod 644 /home/ctf/flag1.txt

echo "FLAG{test_root_flag}" > /root/flag2.txt
chmod 600 /root/flag2.txt

# Start Flask app as ctf user
cd /app
exec su -c "python app.py" ctf
EOF

RUN chmod +x /entrypoint.sh

# Copy application
WORKDIR /app
COPY app.py /app/

# Expose ports
EXPOSE 8001 22

ENTRYPOINT ["/entrypoint.sh"]

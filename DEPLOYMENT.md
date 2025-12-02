# Deployment Guide - Ubuntu Server

This guide assumes you're deploying to the same server as your SAME encoder/decoder project.

## Prerequisites

- Ubuntu server with NGINX already configured
- Python 3.8+ installed
- DNS record for `dualtone.joshcheshire.com` pointing to your server
- Existing SAME project running on port 8000

## Deployment Steps

### 1. Clone Repository

```bash
cd ~
git clone https://github.com/yourusername/Dual-Tone-Decoder.git
cd Dual-Tone-Decoder
```

### 2. Setup Python Backend

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Create environment file
cp .env.example .env

# Edit if needed (defaults should work)
nano .env
```

Contents of `.env`:
```env
DATABASE_URL=sqlite+aiosqlite:///./tone_decoder.db
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=.wav
FREQUENCY_TOLERANCE_HZ=2.0
```

### 4. Test Backend Locally

```bash
# Still in ~/Dual-Tone-Decoder with venv activated
cd backend && uvicorn main:app --host 127.0.0.1 --port 8001

# In another terminal, test:
curl http://localhost:8001/health
# Should return: {"status":"healthy"}

# If working, stop with Ctrl+C
```

### 5. Create Systemd Service

Edit the service file to use your home directory and port 8001:

```bash
nano tone-decoder.service.example
```

Update paths (replace `yourusername` with your actual username):
```ini
[Unit]
Description=Dual-Tone Sequential Paging Decoder
After=network.target

[Service]
Type=simple
User=yourusername
Group=yourusername
WorkingDirectory=/home/yourusername/Dual-Tone-Decoder/backend
Environment="PATH=/home/yourusername/Dual-Tone-Decoder/venv/bin"
ExecStart=/home/yourusername/Dual-Tone-Decoder/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Install the service:
```bash
sudo cp tone-decoder.service.example /etc/systemd/system/tone-decoder.service
sudo systemctl daemon-reload
sudo systemctl enable tone-decoder
sudo systemctl start tone-decoder
```

Check status:
```bash
sudo systemctl status tone-decoder
```

### 6. Deploy Frontend to /var/www

Copy frontend files to be served by NGINX:

```bash
# Create directory
sudo mkdir -p /var/www/dualtone

# Copy frontend files
sudo cp ~/Dual-Tone-Decoder/frontend/index.html /var/www/dualtone/
sudo cp -r ~/Dual-Tone-Decoder/frontend/static /var/www/dualtone/

# Set ownership (replace 'yourusername' with your username)
sudo chown -R www-data:www-data /var/www/dualtone

# Verify structure
ls -la /var/www/dualtone
# Should show:
# index.html
# static/
#   ├── css/
#   │   └── styles.css
#   └── js/
#       └── app.js
```

### 7. Configure NGINX

Create NGINX site configuration:

```bash
sudo nano /etc/nginx/sites-available/dualtone
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name dualtone.joshcheshire.com;

    root /var/www/dualtone;
    index index.html;

    # Serve static files directly from NGINX
    location / {
        try_files $uri $uri/ /index.html;
    }

    location /static/ {
        alias /var/www/dualtone/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Proxy API calls to Python backend
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase upload size for audio files
        client_max_body_size 50M;

        # Timeouts for longer audio processing
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8001;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/dualtone /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. Setup SSL/HTTPS with Let's Encrypt

```bash
sudo certbot --nginx -d dualtone.joshcheshire.com
```

Follow the prompts. Certbot will automatically update your NGINX config.

### 9. Verify Deployment

```bash
# Check backend service
sudo systemctl status tone-decoder

# Check backend directly
curl http://localhost:8001/health

# Check through NGINX
curl http://dualtone.joshcheshire.com/health

# Open in browser
# http://dualtone.joshcheshire.com (or https if SSL configured)
```

## File Structure on Server

```
/home/yourusername/
├── same-endec/              # Your existing SAME project
│   └── backend/             # SAME backend running on port 8000
└── Dual-Tone-Decoder/       # This project
    ├── backend/             # Tone decoder backend on port 8001
    ├── frontend/            # Source files (not served from here)
    ├── venv/
    ├── tone_decoder.db      # SQLite database (created on first run)
    ├── uploads/             # Temporary audio uploads
    └── .env

/var/www/
├── same-endec/              # Your existing SAME frontend
└── dualtone/                # Dual-tone frontend (served by NGINX)
    ├── index.html
    └── static/
        ├── css/
        │   └── styles.css
        └── js/
            └── app.js

/etc/systemd/system/
├── same-endec.service       # Your existing service
└── tone-decoder.service     # New service for this project

/etc/nginx/sites-available/
├── same                     # Your existing NGINX config
└── dualtone                 # New NGINX config
```

## Port Assignments

- **Port 8000**: SAME encoder/decoder backend
- **Port 8001**: Dual-Tone decoder backend
- **Port 80/443**: NGINX serving both via different hostnames

## Managing the Service

```bash
# Start
sudo systemctl start tone-decoder

# Stop
sudo systemctl stop tone-decoder

# Restart
sudo systemctl restart tone-decoder

# View logs
sudo journalctl -u tone-decoder -f

# Check status
sudo systemctl status tone-decoder
```

## Updating the Application

```bash
cd ~/Dual-Tone-Decoder

# Pull latest changes
git pull

# Activate venv
source venv/bin/activate

# Update dependencies if needed
pip install -r requirements.txt

# Copy updated frontend files to /var/www
sudo cp ~/Dual-Tone-Decoder/frontend/index.html /var/www/dualtone/
sudo cp -r ~/Dual-Tone-Decoder/frontend/static/* /var/www/dualtone/static/

# Restart backend service
sudo systemctl restart tone-decoder

# Clear NGINX cache if needed
sudo systemctl reload nginx
```

## Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u tone-decoder -n 50

# Try running manually to see errors
cd ~/Dual-Tone-Decoder
source venv/bin/activate
cd backend && uvicorn main:app --host 127.0.0.1 --port 8001
```

### Port already in use
```bash
# Check what's using port 8001
sudo lsof -i :8001

# If needed, change port in:
# - /etc/systemd/system/tone-decoder.service
# - /etc/nginx/sites-available/dualtone
```

### NGINX errors
```bash
# Test configuration
sudo nginx -t

# Check NGINX logs
sudo tail -f /var/log/nginx/error.log
```

### Database permissions
```bash
cd ~/Dual-Tone-Decoder
chmod 664 tone_decoder.db
chmod 775 .
```

### File upload issues
```bash
# Ensure uploads directory exists and is writable
mkdir -p ~/Dual-Tone-Decoder/uploads
chmod 755 ~/Dual-Tone-Decoder/uploads
```

## Security Considerations

1. **Firewall**: Only ports 80 and 443 should be open externally
   ```bash
   sudo ufw status
   ```

2. **Backend binding**: Backend only listens on 127.0.0.1 (localhost), not 0.0.0.0

3. **File uploads**: Temporary files are deleted after processing

4. **Database**: SQLite file in project directory, not web-accessible

## Cleanup and Maintenance

### Orphaned File Cleanup

Uploaded audio files are automatically deleted after processing. However, if cleanup fails (rare), orphaned files may accumulate. Set up a cron job to clean old files:

```bash
# Edit crontab
crontab -e

# Add this line to clean files older than 1 hour, every hour
0 * * * * find ~/Dual-Tone-Decoder/uploads -type f -mmin +60 -delete 2>/dev/null
```

Or create a cleanup script:

```bash
# Create cleanup script
cat > ~/Dual-Tone-Decoder/cleanup-uploads.sh << 'EOF'
#!/bin/bash
# Clean up orphaned audio files older than 1 hour
UPLOAD_DIR="$HOME/Dual-Tone-Decoder/uploads"
find "$UPLOAD_DIR" -type f -name "*.wav" -mmin +60 -delete
EOF

chmod +x ~/Dual-Tone-Decoder/cleanup-uploads.sh

# Add to crontab
crontab -e
# Add: 0 * * * * /home/yourusername/Dual-Tone-Decoder/cleanup-uploads.sh
```

### Monitoring Disk Usage

Check uploads directory periodically:

```bash
# Check number of files
ls -1 ~/Dual-Tone-Decoder/uploads | wc -l

# Check disk usage
du -sh ~/Dual-Tone-Decoder/uploads
```

Normal state: 0-2 files (only during active processing)

If you see many files accumulated, cleanup failed and the cron job will remove them.

## Backup

Important files to backup:
```bash
# Database (contains your tone table entries)
~/Dual-Tone-Decoder/tone_decoder.db

# Configuration
~/Dual-Tone-Decoder/.env

# (Optional) Service file if customized
/etc/systemd/system/tone-decoder.service

# (Optional) NGINX config if customized
/etc/nginx/sites-available/dualtone
```

**Note:** You do NOT need to backup the `uploads/` directory - files are temporary and deleted after processing.

Example backup:
```bash
# Create backup directory
mkdir -p ~/backups/tone-decoder

# Backup database
cp ~/Dual-Tone-Decoder/tone_decoder.db ~/backups/tone-decoder/tone_decoder.db.$(date +%Y%m%d)

# Backup config
cp ~/Dual-Tone-Decoder/.env ~/backups/tone-decoder/.env.$(date +%Y%m%d)
```

## Next Steps

After deployment:
1. Add your local tone table entries via the web interface
2. Test with sample audio files (see TESTING.md)
3. Adjust `FREQUENCY_TOLERANCE_HZ` in `.env` if needed based on your results
4. Consider setting up automated backups of `tone_decoder.db`

# Dual-Tone Sequential Paging Decoder

A web-based tool for decoding two-tone sequential paging signals used by fire and EMS services. Upload audio files containing Motorola Quick Call II and other dual-tone formats to identify the frequencies and determine which unit was paged.

## Features

- **Audio Processing**: Detects two-tone sequential signals in WAV audio files
- **Frequency Detection**: Uses Goertzel algorithm for accurate frequency identification (±2.0 Hz tolerance)
- **Configurable Tone Tables**: Manage custom tone-to-unit mappings via web interface
- **Real-time Results**: Displays detected frequencies, confidence levels, and matched units
- **Local Processing**: All processing happens on your server - no third-party dependencies
- **Security Hardened**: Rate limiting, input validation, path traversal protection

## Documentation

- **[Deployment Guide](DEPLOYMENT.md)** - Complete guide for deploying to Ubuntu server with NGINX
- **[Testing Guide](TESTING.md)** - Testing procedures and sample audio generation
- **[Security Documentation](SECURITY.md)** - Security measures, limitations, and best practices

## Technology Stack

- **Backend**: Python 3.8+, FastAPI
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Audio Processing**: librosa, scipy, numpy
- **Database**: SQLite (via SQLAlchemy async)
- **Security**: SlowAPI rate limiting, input sanitization

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
cd Dual-Tone-Decoder
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment configuration:
```bash
cp .env.example .env
```

5. (Optional) Edit `.env` to customize settings:
```
DATABASE_URL=sqlite+aiosqlite:///./tone_decoder.db
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=.wav
FREQUENCY_TOLERANCE_HZ=2.0
```

## Quick Start

### Development/Local Testing

```bash
# Use the included start script
./start.sh
```

Or manually:
```bash
source venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Then open your browser to: `http://localhost:8000`

### Production Deployment

For production deployment to Ubuntu server with NGINX, see **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete instructions.

## Usage

### Decoding Audio Files

1. Click "Upload Audio File" or drag and drop a WAV file
2. Click "Decode Audio" to process
3. View detected frequencies and matched unit (if in database)

### Managing Tone Tables

1. Scroll to "Tone Table Management" section
2. Click "Add Entry" to create new tone mappings
3. Fill in:
   - **Label**: Unit identifier (e.g., "Station 1", "Engine 42")
   - **Tone 1 (Hz)**: First tone frequency
   - **Tone 2 (Hz)**: Second tone frequency
4. Click "Save All Changes" to persist

### Supported Formats

Currently supports:
- **WAV files** (PCM, mono or stereo)

Planned support:
- MP3 (future enhancement)
- Other common audio formats

## Audio Processing Details

### Detection Parameters

- **Tone 1 Duration**: ~1 second
- **Tone 2 Duration**: ~3 seconds
- **Gap Between Tones**: 0-500ms
- **Frequency Range**: 200-3000 Hz
- **Tolerance**: ±2.0 Hz

### Supported Paging Standards

Primary support for:
- Motorola Quick Call II (One Plus One)
- Motorola Two-Tone Sequential

Reference document included: `tone-signaling-charts.pdf`

## API Endpoints

### Tone Entry Management

- `GET /api/tones/` - List all tone entries
- `GET /api/tones/{id}` - Get specific entry
- `POST /api/tones/` - Create new entry
- `PUT /api/tones/{id}` - Update entry
- `DELETE /api/tones/{id}` - Delete entry

### Audio Decoding

- `POST /api/decode/` - Upload and decode audio file

### System

- `GET /health` - Health check endpoint


## Configuration

Edit `.env` file to customize:

- `DATABASE_URL`: SQLite database location
- `UPLOAD_DIR`: Temporary upload directory
- `MAX_FILE_SIZE_MB`: Maximum file upload size
- `ALLOWED_EXTENSIONS`: Comma-separated list of allowed file extensions
- `FREQUENCY_TOLERANCE_HZ`: Matching tolerance for frequency detection

## Troubleshooting

For troubleshooting deployment issues, see **[DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting)**.

Common issues:
- **Audio file won't decode**: Ensure file is WAV format, under 50MB, with clear tones
- **No matches found**: Add tone entries via web interface, verify frequencies are correct
- **Rate limited**: Wait 1 minute (10 uploads/minute limit per IP address)

## Security

This application includes:
- Rate limiting to prevent abuse
- Input validation and sanitization
- Path traversal protection
- Memory exhaustion prevention

**Important:** No authentication is implemented by default. For production deployment, add Basic Auth via NGINX or implement API keys. See **[SECURITY.md](SECURITY.md)** for details.

## Contributing

To customize for your region:

1. Obtain official tone frequency documentation from your dispatch center
2. Add entries via the web interface
3. Adjust `FREQUENCY_TOLERANCE_HZ` in `.env` based on your radio system characteristics

## Acknowledgments

- Frequency reference data from Midian Electronics tone signaling charts
- Built for fire and EMS services to improve dispatch operations

## License

This project is provided as-is for use by fire and EMS services for decoding paging tones.

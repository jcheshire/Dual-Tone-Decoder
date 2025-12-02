# Dual-Tone Sequential Paging Decoder

A web-based tool for decoding two-tone sequential paging signals used by fire and EMS services. Upload audio files containing Motorola Quick Call II and other dual-tone formats to identify the frequencies and determine which unit was paged.

## Features

- **Audio Processing**: Detects two-tone sequential signals in WAV audio files
- **Frequency Detection**: Uses Goertzel algorithm for accurate frequency identification (±2.0 Hz tolerance)
- **Configurable Tone Tables**: Manage custom tone-to-unit mappings via web interface
- **Real-time Results**: Displays detected frequencies, confidence levels, and matched units
- **Local Processing**: All processing happens on your server - no third-party dependencies

## Technology Stack

- **Backend**: Python 3.8+, FastAPI
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Audio Processing**: librosa, scipy, numpy
- **Database**: SQLite (via SQLAlchemy async)

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

## Running the Application

1. Start the server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Open your browser to:
```
http://localhost:8000
```

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

## Deployment

### Ubuntu Server Deployment

1. Install system dependencies:
```bash
sudo apt update
sudo apt install python3-pip python3-venv libsndfile1 ffmpeg
```

2. Follow installation steps above

3. Run with production server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

4. (Recommended) Set up as systemd service:

Create `/etc/systemd/system/tone-decoder.service`:
```ini
[Unit]
Description=Dual-Tone Decoder
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/Dual-Tone-Decoder
Environment="PATH=/path/to/Dual-Tone-Decoder/venv/bin"
ExecStart=/path/to/Dual-Tone-Decoder/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tone-decoder
sudo systemctl start tone-decoder
```

5. (Recommended) Set up nginx reverse proxy for HTTPS

## Configuration

Edit `.env` file to customize:

- `DATABASE_URL`: SQLite database location
- `UPLOAD_DIR`: Temporary upload directory
- `MAX_FILE_SIZE_MB`: Maximum file upload size
- `ALLOWED_EXTENSIONS`: Comma-separated list of allowed file extensions
- `FREQUENCY_TOLERANCE_HZ`: Matching tolerance for frequency detection

## Troubleshooting

### Audio file won't decode
- Ensure file is WAV format
- Check file size is under 50MB
- Verify tones are clearly audible
- Try increasing `FREQUENCY_TOLERANCE_HZ` in `.env`

### No matches found
- Add tone entries to the database via the web interface
- Verify frequencies are correct (reference your dispatch documentation)
- Check detected frequencies against your tone table

### Performance issues
- Increase server resources
- Reduce `MAX_FILE_SIZE_MB` if processing large files
- Run with multiple workers: `--workers 4`

## License

This project is provided as-is for use by fire and EMS services for decoding paging tones.

## Contributing

To customize for your region:

1. Obtain official tone frequency documentation from your dispatch center
2. Add entries via the web interface or directly to the database
3. Adjust `FREQUENCY_TOLERANCE_HZ` based on your radio system characteristics

## Acknowledgments

- Frequency reference data from Midian Electronics tone signaling charts
- Built for fire and EMS services to improve dispatch operations

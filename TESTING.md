# Testing Guide

## Quick Start Testing

### 1. Install and Run

```bash
# Make start script executable (if not already)
chmod +x start.sh

# Run the application
./start.sh
```

The application will be available at: http://localhost:8000

### 2. Generate Test Tones

You can generate test two-tone audio files using online tone generators:

**Recommended generators:**
- Audacity (free desktop software)
- Online Tone Generator websites (search for "two tone generator")

**Example test tones (Motorola Quick Call II):**

From Group 1 (tone-signaling-charts.pdf page 1):
- Tone 111: 349.0 Hz
- Tone 112: 368.5 Hz
- Tone 113: 389.0 Hz

**Creating a test file in Audacity:**
1. Generate > Tone
2. Waveform: Sine
3. Frequency: 349.0 Hz
4. Duration: 1 second
5. Click "Generate"
6. Position cursor at 1 second
7. Generate > Tone
8. Frequency: 368.5 Hz
9. Duration: 3 seconds
10. File > Export > Export as WAV

### 3. Add Test Entries to Database

1. Open http://localhost:8000
2. Scroll to "Tone Table Management"
3. Click "Add Entry"
4. Fill in:
   - Label: `Test Station 1`
   - Tone 1: `349.0`
   - Tone 2: `368.5`
5. Click "Save All Changes"

### 4. Test Decoding

1. Click "Upload Audio File"
2. Select your test WAV file
3. Click "Decode Audio"
4. Verify results:
   - Tone 1 should show ~349.0 Hz
   - Tone 2 should show ~368.5 Hz
   - Should match "Test Station 1"
   - Confidence should be high (>80%)

## API Testing with curl

### Health Check
```bash
curl http://localhost:8000/health
```

### List Tone Entries
```bash
curl http://localhost:8000/api/tones/
```

### Create Tone Entry
```bash
curl -X POST http://localhost:8000/api/tones/ \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Engine 1",
    "tone1_hz": 600.9,
    "tone2_hz": 634.5
  }'
```

### Upload Audio for Decoding
```bash
curl -X POST http://localhost:8000/api/decode/ \
  -F "file=@/path/to/test.wav"
```

### Update Tone Entry
```bash
curl -X PUT http://localhost:8000/api/tones/1 \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Engine 1 Updated",
    "tone1_hz": 600.9,
    "tone2_hz": 634.5
  }'
```

### Delete Tone Entry
```bash
curl -X DELETE http://localhost:8000/api/tones/1
```

## Common Test Scenarios

### Scenario 1: Perfect Match
- Upload audio with clear tones
- Tones exactly match database entry
- Expected: High confidence, matched entry found

### Scenario 2: Close Match (Within Tolerance)
- Upload audio with tones 349.5 Hz and 368.8 Hz
- Database has entry: 349.0 Hz and 368.5 Hz
- Expected: Match found (within ±2.0 Hz tolerance)

### Scenario 3: No Match
- Upload audio with tones not in database
- Expected: Tones detected, but "no matching entry in database"

### Scenario 4: No Tones Detected
- Upload audio with no clear two-tone sequence
- Expected: "No two-tone sequence detected"

### Scenario 5: Noisy Audio
- Upload audio with background noise
- Expected: May detect tones with lower confidence

## Troubleshooting Tests

### Test fails: "Failed to load audio file"
- Ensure file is WAV format
- Check file is not corrupted
- Try re-exporting from audio editor

### Test fails: Tones not detected
- Verify tones are audible in audio editor
- Check tone duration (1s + 3s)
- Ensure tones are in 200-3000 Hz range
- Try generating cleaner tones

### Test fails: Wrong frequencies detected
- Check if audio has background noise
- Verify original tone frequencies
- Try increasing volume/amplitude
- Ensure tones are pure sine waves

### Test fails: Match not found despite correct tones
- Check tolerance setting (default ±2.0 Hz)
- Verify database entry exists
- Check for typos in frequency values
- Try increasing `FREQUENCY_TOLERANCE_HZ` in .env

## Performance Testing

### Test with various file sizes:
```bash
# Small file (10 seconds)
# Medium file (60 seconds)
# Large file (5 minutes)
```

Expected processing time: < 5 seconds for typical dispatch audio

### Concurrent uploads:
Test with multiple simultaneous uploads to verify server handles load.

## Production Readiness Checklist

- [ ] Test with real dispatch audio recordings
- [ ] Populate database with all local tone codes
- [ ] Verify tolerance matches your radio system
- [ ] Test on Ubuntu deployment server
- [ ] Configure systemd service
- [ ] Set up HTTPS (if public-facing)
- [ ] Test database backup/restore
- [ ] Document tone codes for your region
- [ ] Train users on the interface

## Motorola Quick Call II Test Frequencies

From included PDF (tone-signaling-charts.pdf):

**Group 1 Test Codes:**
- 111-121: 349.0 Hz → 600.9 Hz
- 112-122: 368.5 Hz → 634.5 Hz
- 113-123: 389.0 Hz → 669.9 Hz

**Group 2 Test Codes:**
- 121-131: 600.9 Hz → 1034.7 Hz
- 122-132: 634.5 Hz → 1063.2 Hz

Use these to create realistic test scenarios.

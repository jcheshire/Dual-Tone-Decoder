// API Configuration
const API_BASE = '/api';

// State management
let selectedFile = null;
let toneEntries = [];
let pendingChanges = new Set();

// DOM Elements
const audioFileInput = document.getElementById('audioFile');
const uploadArea = document.getElementById('uploadArea');
const fileInfo = document.getElementById('fileInfo');
const decodeBtn = document.getElementById('decodeBtn');
const resultsSection = document.getElementById('resultsSection');
const tone1Result = document.getElementById('tone1Result');
const tone2Result = document.getElementById('tone2Result');
const confidenceResult = document.getElementById('confidenceResult');
const matchedEntry = document.getElementById('matchedEntry');
const matchedLabel = document.getElementById('matchedLabel');
const resultMessage = document.getElementById('resultMessage');
const toneTableBody = document.getElementById('toneTableBody');
const addRowBtn = document.getElementById('addRowBtn');
const saveTableBtn = document.getElementById('saveTableBtn');
const loadTableBtn = document.getElementById('loadTableBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadToneTable();
});

function initializeEventListeners() {
    // File upload
    audioFileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect({ target: { files } });
        }
    });

    // Decode button
    decodeBtn.addEventListener('click', decodeAudio);

    // Table management
    addRowBtn.addEventListener('click', addNewRow);
    saveTableBtn.addEventListener('click', saveAllChanges);
    loadTableBtn.addEventListener('click', loadToneTable);
}

function handleFileSelect(event) {
    const file = event.target.files[0];

    if (!file) return;

    // Validate file type
    if (!file.name.toLowerCase().endsWith('.wav')) {
        showNotification('Please select a WAV file', 'error');
        return;
    }

    // Validate file size (50MB)
    if (file.size > 50 * 1024 * 1024) {
        showNotification('File is too large. Maximum size is 50MB', 'error');
        return;
    }

    selectedFile = file;
    fileInfo.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
    fileInfo.style.display = 'block';
    decodeBtn.disabled = false;
}

async function decodeAudio() {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    decodeBtn.classList.add('loading');
    decodeBtn.disabled = true;
    resultsSection.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/decode/`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to decode audio');
        }

        const result = await response.json();
        displayResults(result);

    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        decodeBtn.classList.remove('loading');
        decodeBtn.disabled = false;
    }
}

function displayResults(result) {
    resultsSection.style.display = 'block';

    if (result.tone1_detected_hz) {
        tone1Result.textContent = `${result.tone1_detected_hz} Hz`;
    } else {
        tone1Result.textContent = 'Not detected';
    }

    if (result.tone2_detected_hz) {
        tone2Result.textContent = `${result.tone2_detected_hz} Hz`;
    } else {
        tone2Result.textContent = 'Not detected';
    }

    confidenceResult.textContent = `${(result.confidence * 100).toFixed(0)}%`;

    if (result.matched_entry) {
        matchedEntry.style.display = 'flex';
        matchedLabel.textContent = result.matched_entry.label;
    } else {
        matchedEntry.style.display = 'none';
    }

    resultMessage.textContent = result.message;

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function loadToneTable() {
    loadTableBtn.classList.add('loading');

    try {
        const response = await fetch(`${API_BASE}/tones/`);

        if (!response.ok) {
            throw new Error('Failed to load tone table');
        }

        toneEntries = await response.json();
        renderToneTable();
        pendingChanges.clear();

    } catch (error) {
        showNotification(`Error loading table: ${error.message}`, 'error');
    } finally {
        loadTableBtn.classList.remove('loading');
    }
}

function renderToneTable() {
    toneTableBody.innerHTML = '';

    toneEntries.forEach(entry => {
        addRowToTable(entry);
    });
}

function addRowToTable(entry = null) {
    const row = document.createElement('tr');
    row.dataset.id = entry ? entry.id : 'new';

    row.innerHTML = `
        <td><input type="text" class="label-input" value="${entry ? entry.label : ''}" placeholder="Enter label"></td>
        <td><input type="number" class="tone1-input" value="${entry ? entry.tone1_hz : ''}" placeholder="Hz" step="0.1"></td>
        <td><input type="number" class="tone2-input" value="${entry ? entry.tone2_hz : ''}" placeholder="Hz" step="0.1"></td>
        <td>
            <button class="btn btn-danger delete-btn">Delete</button>
        </td>
    `;

    // Add event listeners
    const inputs = row.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            pendingChanges.add(row.dataset.id);
        });
    });

    const deleteBtn = row.querySelector('.delete-btn');
    deleteBtn.addEventListener('click', () => deleteRow(row));

    toneTableBody.appendChild(row);
}

function addNewRow() {
    addRowToTable();
    pendingChanges.add('new');
}

async function deleteRow(row) {
    const id = row.dataset.id;

    if (id === 'new') {
        row.remove();
        pendingChanges.delete('new');
        return;
    }

    if (!confirm('Are you sure you want to delete this entry?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/tones/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete entry');
        }

        row.remove();
        toneEntries = toneEntries.filter(e => e.id != id);
        pendingChanges.delete(id);
        showNotification('Entry deleted successfully', 'success');

    } catch (error) {
        showNotification(`Error deleting entry: ${error.message}`, 'error');
    }
}

async function saveAllChanges() {
    if (pendingChanges.size === 0) {
        showNotification('No changes to save', 'info');
        return;
    }

    saveTableBtn.classList.add('loading');
    let successCount = 0;
    let errorCount = 0;

    for (const id of pendingChanges) {
        const row = document.querySelector(`tr[data-id="${id}"]`);
        if (!row) continue;

        const label = row.querySelector('.label-input').value.trim();
        const tone1 = parseFloat(row.querySelector('.tone1-input').value);
        const tone2 = parseFloat(row.querySelector('.tone2-input').value);

        // Validate
        if (!label || !tone1 || !tone2) {
            showNotification('Please fill all fields', 'error');
            errorCount++;
            continue;
        }

        try {
            if (id === 'new') {
                // Create new entry
                const response = await fetch(`${API_BASE}/tones/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        label: label,
                        tone1_hz: tone1,
                        tone2_hz: tone2
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to create entry');
                }

                const newEntry = await response.json();
                row.dataset.id = newEntry.id;
                toneEntries.push(newEntry);
                successCount++;

            } else {
                // Update existing entry
                const response = await fetch(`${API_BASE}/tones/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        label: label,
                        tone1_hz: tone1,
                        tone2_hz: tone2
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to update entry');
                }

                const updatedEntry = await response.json();
                const index = toneEntries.findIndex(e => e.id == id);
                if (index !== -1) {
                    toneEntries[index] = updatedEntry;
                }
                successCount++;
            }

        } catch (error) {
            showNotification(`Error saving entry: ${error.message}`, 'error');
            errorCount++;
        }
    }

    saveTableBtn.classList.remove('loading');
    pendingChanges.clear();

    if (successCount > 0) {
        showNotification(`Successfully saved ${successCount} entries`, 'success');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.style.display = 'block';

    setTimeout(() => {
        notification.style.display = 'none';
    }, 5000);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

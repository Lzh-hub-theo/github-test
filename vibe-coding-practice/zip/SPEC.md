# Image Compressor - Project Specification

## 1. Project Overview

- **Project**: Image Compressor
- **Type**: Full-stack web application (single-page + REST API)
- **Core functionality**: Upload, compress, and download images with quality control and side-by-side comparison
- **Target users**: Anyone needing to reduce image file sizes

## 2. Architecture

```
image-compressor/
├── SPEC.md
├── server.py           # Flask API server
├── requirements.txt    # Python dependencies
├── public/
│   └── index.html     # Frontend SPA
├── Makefile
├── AGENTS.md
├── PLANS.md
└── docs/
    ├── ARCHITECTURE.md
    └── OBSERVABILITY.md
```

## 3. Functionality Specification

### 3.1 Image Upload
- Drag-and-drop zone with visual feedback (border highlight, icon change)
- Click to open file picker
- Accept formats: JPG/JPEG, PNG, WebP
- Support multiple file selection (batch processing)
- Max file size: 50MB per file
- Client-side validation before upload

### 3.2 Compression Settings
- Quality presets: High (80%), Medium (60%), Low (40%)
- Custom quality slider: 10% - 100%
- Output format selection: Original, JPG, PNG, WebP
- Real-time quality preview

### 3.3 Comparison Display
- Side-by-side preview: Original vs Compressed
- Display for each image:
  - Filename
  - Dimensions (width x height)
  - File size (KB/MB)
  - Compression ratio percentage
- Visual indicator showing size reduction

### 3.4 Download
- Individual download button per image
- "Download All" button for batch (creates ZIP)
- Filename pattern: `{original_name}_compressed.{ext}`

### 3.5 UI/UX
- Modern minimalist design with green accent (#10B981)
- Responsive layout (mobile-first)
- Upload progress indicator
- Toast notifications for success/error states
- Smooth animations for transitions

## 4. API Endpoints

### POST /api/compress
- **Request**: multipart/form-data with image file + quality + format
- **Response**: JSON with compressed image data (base64) + metadata
- **Fields**: `file`, `quality` (10-100), `output_format` (original|jpg|png|webp)

### GET /api/health
- Health check endpoint
- **Response**: `{ "status": "ok" }`

## 5. Technical Stack

- **Backend**: Python 3.8+, Flask, Pillow
- **Frontend**: Vanilla HTML/CSS/JS (no framework)
- **Build**: Single `server.py` entry point

## 6. Acceptance Criteria

- [ ] User can upload images via drag-drop or file picker
- [ ] User can select compression quality (preset or custom)
- [ ] User can select output format
- [ ] Comparison view shows original vs compressed with metadata
- [ ] Download works for single files and batch (ZIP)
- [ ] Mobile responsive design
- [ ] Green color scheme applied
- [ ] Project runs with single `python server.py` command
"""Image Compressor - Flask API Server"""
import base64
import io
import json
import os
import uuid
import zipfile
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_file
from PIL import Image

app = Flask(__name__, static_folder='public', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

TRACE_ID_HEADER = 'X-Trace-ID'
RUN_ID_HEADER = 'X-Run-ID'

def log_event(event_name, trace_id=None, run_id=None, **fields):
    """Structured logging for observability."""
    entry = {
        "event": event_name,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "trace_id": trace_id or "local",
        "run_id": run_id or str(uuid.uuid4())[:8],
    }
    entry.update(fields)
    print(json.dumps(entry))

def compress_image(image_data, quality=80, output_format=None):
    """Compress image and return (compressed_bytes, metadata)."""
    img = Image.open(io.BytesIO(image_data))

    output = io.BytesIO()
    format_map = {
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'png': 'PNG',
        'webp': 'WEBP'
    }
    img_format = format_map.get(output_format, img.format or 'JPEG')

    # Convert RGBA to RGB for JPEG format
    if img.mode == 'RGBA' and img_format == 'JPEG':
        img = img.convert('RGB')

    if img_format == 'PNG':
        # PNG is lossless - quality maps to compress_level (0-9)
        # quality 100 -> compress_level 0 (no compression, larger)
        # quality 10  -> compress_level 9 (max compression, smaller)
        # Note: For photo-like images, PNG re-compression may not reduce size much
        compress_level = int((100 - quality) / 11.1)  # 100->9, 0->0 roughly
        compress_level = min(9, max(0, compress_level))
        save_kwargs = {'compress_level': compress_level, 'optimize': False}
    elif img_format == 'WEBP':
        # WebP lossy compression - quality 0-100
        save_kwargs = {'quality': quality, 'method': 6}
    else:
        # JPEG lossy compression - quality 0-100
        save_kwargs = {'quality': quality, 'optimize': True}

    img.save(output, format=img_format, **save_kwargs)
    compressed_data = output.getvalue()

    return compressed_data, {
        "width": img.width,
        "height": img.height,
        "format": img_format,
        "mode": img.mode
    }

@app.before_request
def before():
    """Add trace/run IDs to request context."""
    request.trace_id = request.headers.get(TRACE_ID_HEADER, str(uuid.uuid4())[:8])
    request.run_id = request.headers.get(RUN_ID_HEADER, str(uuid.uuid4())[:8])

@app.after_request
def after(response):
    """Add trace headers to response."""
    response.headers[TRACE_ID_HEADER] = request.trace_id
    response.headers[RUN_ID_HEADER] = request.run_id
    return response

@app.route('/api/health')
def health():
    """Health check endpoint."""
    log_event("health_check", status="ok", trace_id=request.trace_id)
    return jsonify({"status": "ok", "trace_id": request.trace_id})

@app.route('/api/compress', methods=['POST'])
def compress():
    """Compress an image file."""
    if 'file' not in request.files:
        log_event("compress_error", error="no_file", trace_id=request.trace_id)
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    quality = request.form.get('quality', 80, type=int)
    quality = max(10, min(100, quality))

    output_format = request.form.get('output_format', 'original')
    if output_format == 'original':
        output_format = None

    allowed_extensions = {'jpg', 'jpeg', 'png', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({"error": f"Unsupported format: {ext}"}), 400

    log_event("compress_start",
        trace_id=request.trace_id,
        filename=file.filename,
        quality=quality,
        output_format=output_format or ext)

    try:
        original_data = file.read()
        original_size = len(original_data)

        compressed_data, metadata = compress_image(original_data, quality, output_format)
        compressed_size = len(compressed_data)

        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

        result = {
            "success": True,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": round(ratio, 1),
            "metadata": metadata,
            "image_data": base64.b64encode(compressed_data).decode('utf-8'),
            "trace_id": request.trace_id
        }

        log_event("compress_success",
            trace_id=request.trace_id,
            original_size=original_size,
            compressed_size=compressed_size,
            ratio=ratio)

        return jsonify(result)

    except Exception as e:
        log_event("compress_error", trace_id=request.trace_id, error=str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/compress-batch', methods=['POST'])
def compress_batch():
    """Compress multiple images and return as ZIP."""
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400

    quality = request.form.get('quality', 80, type=int)
    quality = max(10, min(100, quality))

    output_format = request.form.get('output_format', 'original')
    if output_format == 'original':
        output_format = None

    log_event("batch_compress_start",
        trace_id=request.trace_id,
        file_count=len(request.files.getlist('files')),
        quality=quality)

    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in request.files.getlist('files'):
                if file.filename:
                    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
                    if ext in {'jpg', 'jpeg', 'png', 'webp'}:
                        original_data = file.read()
                        compressed_data, metadata = compress_image(original_data, quality, output_format)

                        out_ext = output_format if output_format else ext
                        base_name = os.path.splitext(file.filename)[0]
                        zf.writestr(f"{base_name}_compressed.{out_ext}", compressed_data)

        zip_buffer.seek(0)

        log_event("batch_compress_success", trace_id=request.trace_id)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='compressed_images.zip'
        )

    except Exception as e:
        log_event("batch_compress_error", trace_id=request.trace_id, error=str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    """Serve the frontend."""
    return send_file('public/index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    log_event("server_start", port=port)
    app.run(host='0.0.0.0', port=port, debug=True)
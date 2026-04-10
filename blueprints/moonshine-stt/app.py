from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from moonshine_voice import (
    ModelArch,
    Transcriber,
    get_model_for_language,
    load_wav_file,
    model_arch_to_string,
)


app = FastAPI(title="Moonshine STT", version="1.0.0")

ARCH_MAP = {
    "tiny": ModelArch.TINY,
    "base": ModelArch.BASE,
    "tiny-streaming": ModelArch.TINY_STREAMING,
    "base-streaming": ModelArch.BASE_STREAMING,
    "small-streaming": ModelArch.SMALL_STREAMING,
    "medium-streaming": ModelArch.MEDIUM_STREAMING,
}

MODEL_CHOICES = {
    "tiny-streaming": {"label": "Tiny Streaming", "cost": "fastest", "arch": "tiny-streaming"},
    "small-streaming": {"label": "Small Streaming", "cost": "balanced", "arch": "small-streaming"},
    "medium-streaming": {"label": "Medium Streaming", "cost": "best quality", "arch": "medium-streaming"},
    "base": {"label": "Base", "cost": "classic", "arch": "base"},
    "tiny": {"label": "Tiny", "cost": "lightweight", "arch": "tiny"},
}


def _pick_arch(raw: str) -> ModelArch:
    key = (raw or "tiny-streaming").strip().lower()
    if key not in ARCH_MAP:
        raise ValueError(f"Unsupported Moonshine model arch: {raw}")
    return ARCH_MAP[key]


def _current_config() -> tuple[str, ModelArch, str]:
    language = os.getenv("MOONSHINE_LANGUAGE", "en").strip().lower()
    arch = _pick_arch(os.getenv("MOONSHINE_MODEL_ARCH", "tiny-streaming"))
    cache_root = os.getenv("MOONSHINE_CACHE_ROOT", "/models")
    return language, arch, cache_root


def _public_path() -> str:
    raw = os.getenv("MOONSHINE_PUBLIC_PATH", "/m")
    path = raw.strip()
    if not path.startswith("/"):
        path = f"/{path}"
    path = path.rstrip("/")
    return path or "/m"


def _model_choice_id_from_env() -> str:
    raw = os.getenv("MOONSHINE_MODEL_CHOICE", "tiny-streaming").strip().lower()
    return raw if raw in MODEL_CHOICES else "tiny-streaming"


def _build_transcriber() -> tuple[Transcriber, str, ModelArch]:
    language, arch, cache_root = _current_config()
    model_path, model_arch = get_model_for_language(
        wanted_language=language,
        wanted_model_arch=arch,
        cache_root=Path(cache_root),
    )
    transcriber = Transcriber(model_path=model_path, model_arch=model_arch)
    return transcriber, model_path, model_arch


def _extract_text(transcript) -> str:
    if transcript is None:
        return ""
    if hasattr(transcript, "text") and transcript.text:
        return str(transcript.text).strip()
    if hasattr(transcript, "lines") and transcript.lines:
        parts = []
        for line in transcript.lines:
            text = getattr(line, "text", "")
            if text:
                parts.append(str(text).strip())
        return " ".join(parts).strip()
    return str(transcript).strip()


def _friendly_model_arch(value) -> str:
    if value is None:
        return "loading..."
    try:
        return model_arch_to_string(value)
    except Exception:
        return str(value)


def _to_wav(input_path: Path) -> Path:
    wav_path = input_path.with_suffix(".wav")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-sample_fmt",
        "s16",
        str(wav_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise HTTPException(
            status_code=400,
            detail=f"Could not convert audio to WAV: {result.stderr.strip() or result.stdout.strip()}",
        )
    return wav_path


@app.on_event("startup")
def startup() -> None:
    transcriber, model_path, model_arch = _build_transcriber()
    app.state.transcriber = transcriber
    app.state.model_path = model_path
    app.state.model_arch = model_arch
    app.state.public_path = _public_path()
    app.state.model_choice = _model_choice_id_from_env()


@app.on_event("shutdown")
def shutdown() -> None:
    transcriber = getattr(app.state, "transcriber", None)
    if transcriber is not None:
        transcriber.close()


@app.get("/")
def root() -> JSONResponse:
    raise HTTPException(status_code=404, detail="Not found")


@app.get(f"{_public_path()}/healthz")
def healthz() -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "model_path": getattr(app.state, "model_path", None),
            "model_arch": _friendly_model_arch(getattr(app.state, "model_arch", None)),
            "public_path": getattr(app.state, "public_path", None),
        }
    )


@app.get(f"{_public_path()}/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    model_path = getattr(app.state, "model_path", "loading...")
    model_arch = _friendly_model_arch(getattr(app.state, "model_arch", None))
    base_path = getattr(app.state, "public_path", _public_path())
    model_choice = getattr(app.state, "model_choice", _model_choice_id_from_env())
    options_html = []
    for key, item in MODEL_CHOICES.items():
        selected = " selected" if key == model_choice else ""
        options_html.append(
            f'<option value="{key}"{selected}>{item["label"]} - {item["cost"]}</option>'
        )
    options_markup = "\n".join(options_html)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Moonshine STT</title>
  <style>
    :root {{
      --bg: #0b1020;
      --panel: rgba(16, 24, 48, 0.86);
      --panel-2: rgba(8, 14, 30, 0.85);
      --text: #eaf0ff;
      --muted: #9fb0d0;
      --accent: #7dd3fc;
      --accent-2: #60a5fa;
      --border: rgba(125, 211, 252, 0.18);
      --shadow: 0 30px 80px rgba(0, 0, 0, 0.35);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(96, 165, 250, 0.28), transparent 38%),
        radial-gradient(circle at 90% 20%, rgba(45, 212, 191, 0.18), transparent 30%),
        linear-gradient(180deg, #050816 0%, #0b1020 100%);
    }}
    .wrap {{
      max-width: 1000px;
      margin: 0 auto;
      padding: 40px 20px 56px;
    }}
    .hero {{
      display: grid;
      gap: 18px;
      margin-bottom: 24px;
    }}
    .kicker {{
      display: inline-flex;
      width: fit-content;
      padding: 6px 12px;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: rgba(255,255,255,0.04);
      color: var(--muted);
      font-size: 13px;
      letter-spacing: 0.03em;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(40px, 7vw, 72px);
      line-height: 0.95;
      letter-spacing: -0.05em;
    }}
    .sub {{
      max-width: 760px;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.6;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 20px;
    }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
    .card {{
      border: 1px solid var(--border);
      border-radius: 24px;
      background: linear-gradient(180deg, var(--panel), var(--panel-2));
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    .card .body {{
      padding: 22px;
    }}
    .drop {{
      border: 1.5px dashed rgba(125, 211, 252, 0.3);
      border-radius: 20px;
      padding: 28px;
      background: rgba(255,255,255,0.03);
    }}
    .drop strong {{ display: block; margin-bottom: 8px; }}
    .muted {{ color: var(--muted); }}
    input[type=file] {{
      width: 100%;
      margin-top: 12px;
      color: var(--muted);
    }}
    .row {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 14px;
      align-items: center;
    }}
    button {{
      border: 0;
      border-radius: 14px;
      padding: 12px 18px;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color: #07111f;
      font-weight: 700;
      cursor: pointer;
    }}
    button:disabled {{
      opacity: 0.6;
      cursor: not-allowed;
    }}
    select {{
      min-width: 220px;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.04);
      color: var(--text);
      padding: 12px 14px;
    }}
    .button-secondary {{
      background: transparent;
      color: var(--text);
      border: 1px solid var(--border);
    }}
    .button-danger {{
      background: linear-gradient(135deg, #fda4af, #fb7185);
      color: #1f0a11;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.04);
      color: var(--muted);
      font-size: 13px;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-wrap: break-word;
      font-size: 15px;
      line-height: 1.6;
      color: #f2f7ff;
    }}
    .result {{
      min-height: 220px;
    }}
    .status {{
      margin-top: 12px;
      color: var(--muted);
      min-height: 24px;
    }}
    .footer {{
      margin-top: 18px;
      font-size: 13px;
      color: var(--muted);
    }}
    a {{ color: var(--accent); }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.95em;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="kicker">Moonshine Voice on your VPS</div>
      <h1>Fast CPU speech-to-text.</h1>
      <div class="sub">
        Upload a WAV file, or let the server convert common audio formats first. This setup uses Moonshine Voice with a tiny streaming model by default, so it stays lightweight on CPU-only boxes.
      </div>
      <div class="row">
        <span class="pill">Model: <code>{model_arch}</code></span>
        <span class="pill">Path: <code>{model_path}</code></span>
      </div>
    </section>

    <div class="grid">
      <div class="card">
        <div class="body">
          <div class="drop">
            <strong>Drop audio here or choose a file</strong>
            <div class="muted">WAV is fastest, but MP3/M4A/OGG should also work because the server normalizes them through ffmpeg.</div>
            <div class="row" style="margin-top:16px;">
              <label class="muted" for="model">Model</label>
              <select id="model">
                {options_markup}
              </select>
            </div>
            <input id="audio" type="file" accept="audio/*,.wav">
            <div class="row">
              <button id="go">Transcribe</button>
              <button id="record" class="button-secondary">Record</button>
              <button id="stop" class="button-danger" disabled>Stop</button>
              <span id="meta" class="muted">Ready when you are.</span>
            </div>
          </div>
          <div class="status" id="status"></div>
        </div>
      </div>

      <div class="card result">
        <div class="body">
          <div class="kicker" style="margin-bottom:14px;">Transcript</div>
          <pre id="output">Upload a file and we'll show the text here.</pre>
        </div>
      </div>
    </div>

    <div class="footer">
      Health check: <a href="{base_path}/healthz">{base_path}/healthz</a> - API: <code>POST {base_path}/api/transcribe</code>
    </div>
  </div>

  <script>
    const audio = document.getElementById('audio');
    const go = document.getElementById('go');
    const record = document.getElementById('record');
    const stop = document.getElementById('stop');
    const model = document.getElementById('model');
    const status = document.getElementById('status');
    const output = document.getElementById('output');
    const meta = document.getElementById('meta');
    const basePath = {base_path!r};
    let mediaStream = null;
    let mediaRecorder = null;
    let chunks = [];

    const preferredMimeTypes = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
    ];

    function pickMimeType() {{
      if (!window.MediaRecorder) return '';
      return preferredMimeTypes.find((type) => MediaRecorder.isTypeSupported(type)) || '';
    }}

    async function uploadBlob(blob, filename) {{
      const form = new FormData();
      form.append('file', blob, filename);
      form.append('model_choice', model.value);
      go.disabled = true;
      record.disabled = true;
      stop.disabled = true;
      status.textContent = 'Transcribing...';
      output.textContent = '';
      meta.textContent = `${{filename}} - ${{Math.round(blob.size / 1024)}} KB`;
      try {{
        const res = await fetch(`${{basePath}}/api/transcribe`, {{ method: 'POST', body: form }});
        const data = await res.json();
        if (!res.ok) {{
          throw new Error(data.detail || 'Transcription failed');
        }}
        output.textContent = data.text || '(no transcript)';
        status.textContent = `Done in ${{data.seconds.toFixed(2)}}s`;
      }} catch (err) {{
        status.textContent = `Error: ${{err.message}}`;
        output.textContent = '';
      }} finally {{
        go.disabled = false;
        record.disabled = false;
      }}
    }}

    async function submit() {{
      if (!audio.files.length) {{
        status.textContent = 'Pick an audio file first.';
        return;
      }}
      const file = audio.files[0];
      await uploadBlob(file, file.name || 'upload.wav');
    }}

    async function startRecording() {{
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
        status.textContent = 'Recording is not supported in this browser.';
        return;
      }}
      try {{
        mediaStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
        chunks = [];
        const mimeType = pickMimeType();
        mediaRecorder = mimeType ? new MediaRecorder(mediaStream, {{ mimeType }}) : new MediaRecorder(mediaStream);
        mediaRecorder.ondataavailable = (event) => {{
          if (event.data && event.data.size > 0) {{
            chunks.push(event.data);
          }}
        }};
        mediaRecorder.onstop = async () => {{
          const blob = new Blob(chunks, {{ type: mediaRecorder.mimeType || 'audio/webm' }});
          const extension = (mediaRecorder.mimeType || 'audio/webm').includes('mp4') ? 'm4a' : 'webm';
          cleanupRecording();
          await uploadBlob(blob, `recording.${{extension}}`);
        }};
        mediaRecorder.start();
        record.disabled = true;
        stop.disabled = false;
        status.textContent = 'Recording...';
        meta.textContent = 'Recording audio from the microphone.';
      }} catch (err) {{
        status.textContent = `Microphone error: ${{err.message}}`;
        cleanupRecording();
      }}
    }}

    function cleanupRecording() {{
      if (mediaStream) {{
        mediaStream.getTracks().forEach((track) => track.stop());
        mediaStream = null;
      }}
      mediaRecorder = null;
      chunks = [];
      record.disabled = false;
      stop.disabled = true;
    }}

    function stopRecording() {{
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
        mediaRecorder.stop();
        status.textContent = 'Finalizing recording...';
      }}
    }}

    go.addEventListener('click', submit);
    record.addEventListener('click', startRecording);
    stop.addEventListener('click', stopRecording);
    audio.addEventListener('change', () => {{
      if (audio.files.length) {{
        const file = audio.files[0];
        meta.textContent = `${{file.name}} - ${{Math.round(file.size / 1024)}} KB`;
      }}
    }});
  </script>
</body>
</html>"""
    return HTMLResponse(html)


@app.post(f"{_public_path()}/api/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    model_choice: str = Form("tiny-streaming"),
) -> JSONResponse:
    transcriber = getattr(app.state, "transcriber", None)
    if transcriber is None:
        raise HTTPException(status_code=503, detail="Transcriber is still starting up")

    requested_choice = (model_choice or "tiny-streaming").strip().lower()
    if requested_choice not in MODEL_CHOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model choice: {requested_choice}",
        )

    current_choice = getattr(app.state, "model_choice", None)
    if current_choice != requested_choice:
        if transcriber is not None:
            transcriber.close()
        language = os.getenv("MOONSHINE_LANGUAGE", "en").strip().lower()
        cache_root = os.getenv("MOONSHINE_CACHE_ROOT", "/models")
        selected_arch = _pick_arch(requested_choice)
        model_path, model_arch = get_model_for_language(
            wanted_language=language,
            wanted_model_arch=selected_arch,
            cache_root=Path(cache_root),
        )
        transcriber = Transcriber(model_path=model_path, model_arch=model_arch)
        app.state.transcriber = transcriber
        app.state.model_path = model_path
        app.state.model_arch = model_arch
        app.state.model_choice = requested_choice

    started = time.perf_counter()
    suffix = Path(file.filename or "upload").suffix.lower() or ".bin"
    with tempfile.TemporaryDirectory(prefix="moonshine-upload-") as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_path = tmpdir_path / f"upload{suffix}"
        with input_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        wav_path = input_path if input_path.suffix == ".wav" else _to_wav(input_path)
        audio_data, sample_rate = load_wav_file(wav_path)
        transcript = transcriber.transcribe_without_streaming(audio_data, sample_rate)
        text = _extract_text(transcript)

    return JSONResponse(
        {
            "text": text,
            "seconds": round(time.perf_counter() - started, 4),
            "sample_rate": sample_rate,
            "file_name": file.filename,
        }
    )

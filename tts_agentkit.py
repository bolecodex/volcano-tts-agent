import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from agentkit.apps import AgentkitSimpleApp

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

app = AgentkitSimpleApp()

try:
    from fastapi.middleware.cors import CORSMiddleware

    cors_origins_raw = (os.getenv("CORS_ORIGINS") or "").strip()
    cors_origins = (
        [o.strip() for o in cors_origins_raw.split(",") if o.strip()]
        if cors_origins_raw
        else ["*"]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )
except Exception:
    pass

def _create_api_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    from backend.api import tts_router
    from backend.models import init_database

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        init_database()
        yield

    api_app = FastAPI(lifespan=lifespan)
    cors_origins_raw = (os.getenv("CORS_ORIGINS") or "").strip()
    cors_origins = (
        [o.strip() for o in cors_origins_raw.split(",") if o.strip()]
        if cors_origins_raw
        else ["*"]
    )
    api_app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )
    api_app.include_router(tts_router, prefix="/api/tts", tags=["TTS"])

    @api_app.get("/")
    async def root():
        return {"status": "ok", "service": "tts-agent"}

    @api_app.get("/health")
    async def health():
        return {"status": "ok", "service": "tts-agent"}

    return api_app


app.mount("/", _create_api_app())


def _sanitize_object_name(name: str) -> str:
    import re

    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "_", name.strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "file"


def _get_tos_client():
    import tos

    ak = os.getenv("TOS_ACCESS_KEY") or os.getenv("VOLCENGINE_ACCESS_KEY") or ""
    sk = os.getenv("TOS_SECRET_KEY") or os.getenv("VOLCENGINE_SECRET_KEY") or ""
    endpoint = os.getenv("TOS_ENDPOINT") or ""
    region = os.getenv("TOS_REGION") or ""

    if not (ak and sk and endpoint and region):
        return None

    return tos.TosClientV2(ak, sk, endpoint, region)


def _upload_file_to_tos(
    local_path: str,
    session_id: str,
    content_type: Optional[str] = None,
) -> Optional[dict]:
    client = _get_tos_client()
    if client is None:
        return None

    bucket = os.getenv("TOS_BUCKET") or ""
    if not bucket:
        return None

    prefix = (os.getenv("TOS_PREFIX") or "tts-agent-output").strip("/")
    expires = int(os.getenv("TOS_URL_EXPIRES", "3600"))

    p = Path(local_path)
    if not p.exists() or not p.is_file():
        return None

    filename = _sanitize_object_name(p.name)
    object_key = f"{prefix}/{session_id}/{filename}"

    inferred_ct = content_type
    if not inferred_ct:
        ext = p.suffix.lower()
        if ext == ".mp3":
            inferred_ct = "audio/mpeg"
        elif ext == ".wav":
            inferred_ct = "audio/wav"
        elif ext == ".ogg":
            inferred_ct = "audio/ogg"
        elif ext == ".pcm":
            inferred_ct = "application/octet-stream"

    client.put_object_from_file(bucket=bucket, key=object_key, file_path=str(p), content_type=inferred_ct)
    url = client.generate_presigned_url("GET", Bucket=bucket, Key=object_key, ExpiresIn=expires)

    return {"bucket": bucket, "key": object_key, "url": url}


def _get_output_dir(session_id: str) -> str:
    base_dir = os.getenv("TTS_AGENT_OUTPUT_DIR")
    if not base_dir:
        base_dir = str(Path("/tmp") / "tts_agent")
    return os.path.join(base_dir, session_id)


@app.entrypoint
async def run(payload: dict, headers: dict):
    from agent import create_tts_pipeline

    prompt = payload.get("prompt") or payload.get("text") or ""
    prompt = prompt.strip()
    if not prompt:
        return {"success": False, "error": "payload.prompt 不能为空"}

    session_id = payload.get("session_id") or headers.get("session_id") or str(uuid.uuid4())
    output_dir = _get_output_dir(session_id)

    pipeline = create_tts_pipeline(
        session_id=session_id,
        output_dir=output_dir,
        persist=False,
    )

    logger.info(
        json.dumps(
            {
                "event": "invoke_start",
                "session_id": session_id,
                "user_id": headers.get("user_id", ""),
            },
            ensure_ascii=False,
        )
    )

    stage1 = await pipeline.stage1_analyze(prompt)
    if not stage1.get("success"):
        return {"success": False, "stage": "analyze", "session_id": session_id, "error": stage1.get("error")}

    stage2 = await pipeline.stage2_match()
    if not stage2.get("success"):
        return {"success": False, "stage": "match", "session_id": session_id, "error": stage2.get("error")}

    stage3 = await pipeline.stage3_synthesize()
    if not stage3.get("success"):
        return {"success": False, "stage": "synthesize", "session_id": session_id, "error": stage3.get("error")}

    upload_enabled = (os.getenv("TOS_UPLOAD_ENABLED") or "").strip().lower() in {"1", "true", "yes", "on"}
    audio_file_urls = []
    merged_audio_url = None

    if upload_enabled:
        try:
            for local_path in stage3.get("audio_files", []) or []:
                uploaded = _upload_file_to_tos(local_path=local_path, session_id=session_id)
                if uploaded:
                    audio_file_urls.append(uploaded)

            merged_path = stage3.get("merged_audio")
            if merged_path:
                merged_audio_url = _upload_file_to_tos(local_path=merged_path, session_id=session_id)
        except Exception as e:
            logger.exception("tos_upload_failed: %s", str(e))

    return {
        "success": True,
        "session_id": session_id,
        "input_type": stage1.get("input_type"),
        "dialogue_list": stage1.get("dialogue_list", []),
        "voice_mapping": stage2.get("voice_mapping", []),
        "audio_files": stage3.get("audio_files", []),
        "merged_audio": stage3.get("merged_audio"),
        "output_dir": stage3.get("output_dir"),
        "audio_file_urls": audio_file_urls,
        "merged_audio_url": merged_audio_url,
    }


@app.ping
def ping() -> str:
    return "pong!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

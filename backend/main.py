import logging

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from tempfile import NamedTemporaryFile
from dotenv import dotenv_values
from minio_client import MinioClient
from io import BytesIO
import os
import uuid
import subprocess
import threading
import torch
import numpy as np
import re
import time

import ChatTTS
from tools.normalizer.zh import normalizer_zh_tn

# 初始化 ChatTTS 模型
chat = ChatTTS.Chat()
chat.normalizer.register("zh", normalizer_zh_tn())
chat.load(source="huggingface")
logger = logging.getLogger('chat_tts')

# 初始化 FastAPI
app = FastAPI()

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态目录
STATIC_DIR = "./static"
HLS_OUTPUT_DIR = os.path.join(STATIC_DIR, "tts_hls")
os.makedirs(HLS_OUTPUT_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 初始化 MinIO
config = dotenv_values(".env")
minio_client = MinioClient(config)
API_KEY = config.get("API_KEY")


def verify_bearer_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少或格式错误的 Authorization 头",
        )
    token = auth_header.split("Bearer ")[-1].strip()
    if token != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无效的 API Token",
        )


# 请求体定义
class TTSRequest(BaseModel):
    text: str
    speaker: str
    temperature: float = 0.3
    top_p: float = 0.7
    top_k: int = 20
    prompt: str = "[oral_2][break_6]"
    lang: str = "zh"
    do_text_normalization: bool = True
    do_homophone_replacement: bool = False
    skip_refine_text: bool = True
    use_decoder: bool = True
    file_name: str = "chattts"


# 断句
def split_text(text: str):
    parts = re.split(r'([。！？.,?\n])', text)
    res_list = [''.join(p).strip() for p in zip(parts[::2], parts[1::2]) if ''.join(p).strip()]
    if not res_list:
        res_list = [text.strip()]
    return res_list


# 保存 MP3 并上传
def save_mp3_and_upload_to_minio(pcm_data: bytes, file_name: str):
    tmp_mp3 = None
    try:
        # 创建唯一临时文件名
        tmp_mp3 = NamedTemporaryFile(delete=False, suffix=f"_{uuid.uuid4().hex}.mp3")
        tmp_mp3_path = tmp_mp3.name
        tmp_mp3.close()  # 关闭文件对象，仅保留路径供 ffmpeg 使用

        # 调用 ffmpeg 转为 MP3
        process = subprocess.Popen([
            'ffmpeg', '-y',  # <== 添加 -y 强制覆盖
            '-f', 's16le', '-ar', '24000', '-ac', '1', '-i', '-',
            '-acodec', 'libmp3lame', '-b:a', '64k', tmp_mp3_path
        ], stdin=subprocess.PIPE)
        process.stdin.write(pcm_data)
        process.stdin.close()
        process.wait()

        # 上传到 MinIO
        with open(tmp_mp3_path, "rb") as f:
            bucket_name, _, object_name, file_obj_name = minio_client.put_object(
                file_name=file_name, data=f, length=os.path.getsize(tmp_mp3_path)
            )
            url = minio_client.get_file_url(bucket_name, object_name)
            logger.error(f"[MP3] Uploaded to MinIO: {url}")

    except Exception as e:
        logger.error(f"[ERROR] MP3 上传失败: {e}")

    finally:
        # 删除临时文件
        if tmp_mp3 and os.path.exists(tmp_mp3.name):
            os.remove(tmp_mp3.name)


@app.post("/tts_stream_hls")
def tts_stream_hls(req: TTSRequest, _: None = Depends(verify_bearer_token)):
    # session_id前面拼上年-月-日_时:分:秒.毫秒
    uuid_str = str(uuid.uuid4())
    now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    session_id = f"{now}_{int(time.time() * 1000) % 1000:03d}_{uuid_str}"
    session_dir = os.path.join(HLS_OUTPUT_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    m3u8_path = os.path.join(session_dir, "index.m3u8")
    m3u8_url = f"/static/tts_hls/{session_id}/index.m3u8"

    ffmpeg = subprocess.Popen([
        "ffmpeg",
        "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", "-",

        "-c:a", "aac",
        "-b:a", "64k",

        # 不强制关键帧，默认情况下语音分段足够
        # "-force_key_frames", "expr:gte(t,n_forced*1.5)",

        "-f", "hls",
        "-hls_time", "0.25",  # ✅ 每段 2 秒，更稳定
        "-hls_list_size", "600",  # ✅ 播放器可访问更久的历史
        "-hls_flags", "append_list",  # ✅ 不删除 ts，避免断流

        m3u8_path
    ], stdin=subprocess.PIPE)

    pcm_buffer = BytesIO()

    def pcm_feeder():
        try:
            spk_path = f"/mnt/sdb4/projects/chat_tts_api/speakers/{req.speaker}.pt"
            spk_emb = torch.load(spk_path)

            infer_params = ChatTTS.Chat.InferCodeParams(
                spk_emb=spk_emb,
                temperature=req.temperature,
                top_P=req.top_p,
                top_K=req.top_k
            )
            refine_params = ChatTTS.Chat.RefineTextParams(
                prompt=req.prompt,
                temperature=req.temperature,
                top_P=req.top_p,
                top_K=req.top_k
            )

            for sentence in split_text(req.text):
                for gen in chat.infer(
                        sentence,
                        stream=True,
                        lang=req.lang,
                        skip_refine_text=req.skip_refine_text,
                        use_decoder=req.use_decoder,
                        do_text_normalization=req.do_text_normalization,
                        do_homophone_replacement=req.do_homophone_replacement,
                        params_infer_code=infer_params,
                        params_refine_text=refine_params
                ):
                    audio = np.array(gen[0])
                    pcm = (audio * 32767).astype(np.int16).tobytes()
                    ffmpeg.stdin.write(pcm)
                    pcm_buffer.write(pcm)

                silence = np.zeros(int(0.01 * 24000), dtype=np.int16).tobytes()
                ffmpeg.stdin.write(silence)
                pcm_buffer.write(silence)

        except Exception as e:
            logger.error(f"[ERROR] PCM 推流失败: {e}")
        finally:
            if ffmpeg.stdin:
                ffmpeg.stdin.close()
            save_mp3_and_upload_to_minio(pcm_buffer.getvalue(), req.file_name)

    threading.Thread(target=pcm_feeder, daemon=True).start()

    for _ in range(300):
        if os.path.exists(m3u8_path):
            break
        time.sleep(0.1)

    return JSONResponse(content={"m3u8": m3u8_url})

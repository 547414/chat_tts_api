# chat_tts_api

ChatTTS的API接口封装，支持HLS流式输出并自动播放，支持多角色语音合成。实测在chrome、edge、企微内置浏览器中均可自动流畅播放。

角色文件在backend/speakers中

# 目录

- [一、效果演示](#一效果演示)
- [二、后端](#二后端)
    - [1.安装并激活虚拟环境，建议python版本为3.11](#1安装并激活虚拟环境建议python版本为311)
    - [2.安装ChatTTS](#2安装chatt)
    - [3.依赖](#3依赖)
    - [4.minio 配置](#4minio-配置)
    - [5.api_key配置](#5api_key配置)
    - [6.启动](#6启动)
- [三、nginx设置](#三nginx设置)
- [四、前端](#四前端)
    - [1.安装node，本项目基于node v20开发](#1安装node本项目基于node-v20开发)
    - [2.安装依赖](#2安装依赖)
    - [3.修改配置](#3修改配置)
    - [4.启动前端](#4启动前端)
- [五、相关项目](#五相关项目)

# 一、效果演示

1.合成文本

```text
以后的许多年里，我不断悟出这话的深意。琳，你真的太聪明了，早在几年前，你就嗅出了知识界的政治风向，做出了一些超前的举动，比如你在教学中，把大部分物理定律和参数都改了名字，欧姆定律改叫电阻定律，麦克斯韦方程改名成电磁方程，普朗克常数叫成了量子常数……你对学生们解释说：所有的科学成果都是广大劳动人民智慧的结晶，那些资产阶级学术权威不过是窃取了这些智慧。但即使这样，你仍然没有被"革命主流"所接纳，看看现在的你，衣袖上没有"革命教职员工"都戴着的红袖章；你两手空空地上来，连一本语录都没资格拿……谁让你出生在旧中国那样一个显赫的家庭，你父母又都是那么著名的学者。
```

1.演示视频：
<video controls width="640">
  <source src="./example/example.mp4" type="video/mp4">
</video>

2.合成音频效果
<audio controls>
  <source src="./example/example.mp3" type="audio/mpeg" />
  Your browser does not support the audio element.
</audio>

# 二、后端

### 1.安装并激活虚拟环境，建议python版本为3.11

```shell
conda create -n env_chat_tts_api python=3.11
conda activate env_chat_tts_api
```

### 2.安装ChatTTS

https://github.com/2noise/ChatTTS

```shell
git clone https://github.com/2noise/ChatTTS.git
cd ChatTTS
pip install -r requirements.txt
pip install -e .
```

### 3.依赖

cuda版本取决于你的显卡，以下是开发过程中使用的版本（NVIDIA L20，python3.11），以ubuntu24为例

```shell
pip install torch==2.4.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu124
pip install poetry -i https://pypi.tuna.tsinghua.edu.cn/simple
cd backend
poetry install

sudo apt install -y ffmpeg # 安装ffmpeg
```

#### 如若需要修改python版本

修改`pyproject.toml`中的python版本为需要的版本，然后删除poetry.lock文件，重新安装依赖。

```shell
rm -f poetry.lock
poetry install
```

### 4.minio 配置

minio是一个开源的对象存储服务，在本项目中会在语音合成完成之后转成mp3格式并上传到minio，如果不需要这个功能请注释掉`main.py`
中的`save_mp3_and_upload_to_minio(pcm_buffer.getvalue(), req.file_name)`。

需要修改.env中的minio相关配置为你自己的minio服务

### 5.api_key配置

在`.env`中设置请求后端需要验证的API_KEY

### 6.启动

```shell
CUDA_VISIBLE_DEVICES=3 uvicorn main:app --host 0.0.0.0 --port 6002
```

# 三、nginx设置

配置文件内容

```nginx
server {
    listen 6001 ssl; # 改成你自己的端口
    server_name xxx.com; # 改成你自己的域名

    ssl_certificate /mnt/sdb4/ssl/xxx.pem; # 改成你自己的ssl证书
    ssl_certificate_key /mnt/sdb4/ssl/xxx.key; # 改成你自己的ssl证书

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 10240M;
    keepalive_timeout 600;
    proxy_read_timeout 600;
    proxy_buffering off;
    proxy_cache off;
    tcp_nopush on;
    tcp_nodelay on;
    chunked_transfer_encoding on;

    # 静态资源 HLS 输出
    location /static/tts_hls/ {
        alias /mnt/sdb4/projects/chat_tts_api/backend/static/tts_hls/; # 改成你自己的目录
        autoindex off;

        # HLS 播放所需 header
        add_header Access-Control-Allow-Origin * always;
        add_header Cache-Control no-cache always;
        add_header Accept-Ranges bytes always;

        # 显式声明类型
        types {
            application/vnd.apple.mpegurl m3u8;
            video/mp2t ts;
        }
        default_type application/octet-stream;
    }

    # FastAPI 反向代理
    location / {
        proxy_pass http://127.0.0.1:6002; # 改成你自己的后端地址
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

# 四、前端

### 1.安装node，本项目基于node v20开发

```shell
sudo apt install nodejs npm
```

### 2.安装依赖

```shell
cd frontend
yarn install
```

### 3.修改配置

在`frontend`目录中的`.env.development`、`.env.test`、`.env.production` 中修改后端地址、前端地址、API_KEY(
需要和.env中的API_KEY一致)

### 4.启动前端

```shell
yarn dev
```

## 五、相关项目

- [ChatTTS](https://github.com/2noise/ChatTTS)
- [ChatTTS_Speaker](https://github.com/6drf21e/ChatTTS_Speaker)
- [nginx](https://nginx.org/)
- [MinIO Server](https://min.io/docs/minio/linux/operations/installation.html)
- [FFmpeg](https://ffmpeg.org/download.html)
- [FastAPI](https://fastapi.tiangolo.com/)
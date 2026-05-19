# =============================================================================
# DouyinLiveRecorder Dockerfile（多阶段构建）
# 支持抖音、TikTok、YouTube等60+平台直播录制工具
# =============================================================================

# -----------------------------------------------------------------------------
# 阶段1：构建阶段 - 安装 Node.js 和 Python 依赖
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js（PyExecJS 运行时需要，用于平台签名算法）
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# 先复制依赖文件以利用 Docker 缓存层
COPY requirements.txt pyproject.toml ./

# 安装 Python 依赖到 --user 目录
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --user -r requirements.txt \
    && rm -rf /tmp/*

# -----------------------------------------------------------------------------
# 阶段2：运行阶段 - 精简生产镜像
# -----------------------------------------------------------------------------
FROM python:3.11-slim

LABEL maintainer="Hmily <ihmily@github>" \
      version="4.0.7" \
      description="支持抖音、TikTok、YouTube等60+平台直播录制工具" \
      url="https://github.com/ihmily/DouyinLiveRecorder"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    TZ=Asia/Shanghai \
    TERM=xterm-256color

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tzdata \
    curl \
    && ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制 Node.js（PyExecJS 运行时需要）
COPY --from=builder /usr/bin/node /usr/bin/node
COPY --from=builder /usr/lib/node_modules /usr/lib/node_modules
COPY --from=builder /usr/local/bin/node /usr/local/bin/node 2>/dev/null || true

# 创建非 root 用户
RUN groupadd --gid 1000 recorder \
    && useradd --uid 1000 --gid recorder --shell /bin/bash --create-home recorder

WORKDIR /app

# 从构建阶段复制 Python --user 安装的依赖
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制应用代码
COPY --chown=recorder:recorder . ./

# 创建运行时目录
RUN mkdir -p logs downloads \
    && chown -R recorder:recorder /app

# 切换到非 root 用户
USER recorder

# 健康检查：每 30 秒检查 Python 和主脚本是否可执行
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; os.path.isfile('main.py') and exit(0)" || exit 1

# 可选 Web UI 端口
EXPOSE 8000

ENTRYPOINT ["python", "main.py"]
FROM mcr.microsoft.com/devcontainers/anaconda:1-3


# Copy environment.yml (if found) to a temp location so we update the environment. Also
# copy "noop.txt" so the COPY instruction does not fail if no environment.yml exists.
COPY environment.yml* .devcontainer/noop.txt /tmp/conda-tmp/


RUN apt-get update && \
    export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y \
        git \
        vim \
        curl \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 설치

COPY ./app/requirements.txt /tmp/app-requirements.txt

RUN pip install -r /tmp/app-requirements.txt 

WORKDIR /workspace
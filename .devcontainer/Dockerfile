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

    WORKDIR /workspace

# -*- docker-image-name: "algoritmosrw/corrector" -*-

FROM ubuntu:focal-20200423

RUN apt-get update && \
    apt-get install --assume-yes --no-install-recommends       \
        gcc g++ gcc-multilib make valgrind clang clang-format  \
        perl python3 openjdk-11-jdk-headless libgtest-dev time \
        python3-jinja2 python3-yaml wspanish

COPY ["*.py", "*.j2", "/"]

USER nobody
WORKDIR /tmp

ENTRYPOINT ["/worker.py"]

# vi:et

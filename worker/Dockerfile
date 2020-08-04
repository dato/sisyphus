# -*- docker-image-name: "fiubatps/sisyphus" -*-

FROM ubuntu:focal-20200423

RUN apt-get update && \
    apt-get install --assume-yes --no-install-recommends       \
        gcc g++ gcc-multilib make valgrind clang clang-format  \
        perl python3 openjdk-11-jdk-headless libgtest-dev time \
        python3-pip wspanish git rustc cargo lua5.3

COPY ["requirements.txt", "/"]

RUN pip3 install -r /requirements.txt

COPY ["worker/*.py", "worker/*.j2", "/"]

USER nobody
WORKDIR /tmp

ENTRYPOINT ["/worker.py"]

# vi:et

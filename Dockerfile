FROM python:3.8-slim-buster

# Install our dependencies.
ADD ["Makefile", "requirements.txt", "/opt/sisyphus/"]
RUN make -C /opt/sisyphus deploy

# Install sisyphus itself.
ADD scripts /opt/sisyphus/bin
ADD sisyphus /opt/sisyphus/sisyphus

# Add sisyphus to $PATH.
ENV PATH "$PATH:/opt/sisyphus/bin"

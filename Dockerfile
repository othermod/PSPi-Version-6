# Toolchain image for building every PSPi component.
FROM ubuntu:26.04

ARG ARDUINO_CLI_VERSION=1.5.1
ARG ARDUINO_AVR_VERSION=1.8.8

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git make gcc \
        gcc-arm-linux-gnueabi libc6-dev-armel-cross \
        gcc-aarch64-linux-gnu libc6-dev-arm64-cross \
        gcc-avr binutils-avr avr-libc \
        device-tree-compiler \
    && rm -rf /var/lib/apt/lists/*

# Arduino AVR core, installed to a fixed path (not $HOME) so the build works
# under whatever UID the container is run as
ENV ARDUINO_DIRECTORIES_DATA=/opt/arduino15
RUN curl -fsSL "https://github.com/arduino/arduino-cli/releases/download/v${ARDUINO_CLI_VERSION}/arduino-cli_${ARDUINO_CLI_VERSION}_Linux_64bit.tar.gz" \
        | tar -xz -C /usr/local/bin arduino-cli \
    && arduino-cli core update-index \
    && arduino-cli core install "arduino:avr@${ARDUINO_AVR_VERSION}" \
    && chmod -R a+rX /opt/arduino15
ENV ARDUINO_AVR=/opt/arduino15/packages/arduino/hardware/avr/${ARDUINO_AVR_VERSION}

ENV HOME=/tmp
WORKDIR /src

FROM ubuntu:20.04

RUN apt-get update -qq -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        wget \
        python3-dev \
        haskell-stack \
        libmecab-dev \
        libicu-dev \
        jq \
        xml2 \
        curl \
        python3-pip \
        git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /exquisite/

RUN git clone https://github.com/LuminosoInsight/wikiparsec && \
    cd wikiparsec && \
    stack clean && \
    stack build && \
    stack install --local-bin-path /usr/bin

ADD . /exquisite/

RUN pip3 install -e .

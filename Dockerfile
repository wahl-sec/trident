FROM ubuntu:impish-20211015

ADD Makefile /
ADD trident /trident
ADD data /data
ADD plugins /plugins
ADD config /config
ADD README.md /
ADD setup.py /

SHELL ["/bin/bash", "-c"]

RUN apt-get -y update \
    && apt-get -y install curl \
    && apt-get -y install software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get -y update \
    && apt-get -y install python3.8 \
    && ln -sf /usr/bin/python3.8 /usr/bin/python3 \
    && apt-get -y install python3-pip \
    && apt-get -y install python3.8-dev \
    && make install

ENTRYPOINT ["python3", "-m", "trident"]
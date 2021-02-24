FROM python:3.7

ADD Makefile /
ADD trident /trident
ADD data /data
ADD plugins /plugins
ADD config /config
ADD README.md /
ADD setup.py /

RUN make install

ENTRYPOINT ["python", "-m", "trident"]
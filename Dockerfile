FROM python:3

WORKDIR /app

RUN apt-get update \
    && apt-get install python3-pip -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/*
    
ADD requirements.txt /app
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

ADD exporter.py /app
EXPOSE 8000

CMD [ "python", "exporter.py", "/config/purifiers.json" ]
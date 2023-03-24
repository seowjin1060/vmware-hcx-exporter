FROM python:3.7-alpine

LABEL NAME=hcx_exporter

WORKDIR .
COPY .

RUN pip install -r requirements.txt . \

EXPOSE 9000

ENV PYTHONUNBUFFERED=1

CMD python main.py
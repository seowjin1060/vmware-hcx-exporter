FROM python:3.7-alpine
LABEL NAME=hcx_exporter
WORKDIR /opt/hcx_exporter/
COPY . /opt/hcx_exporter/
RUN pip install -r requirements.txt
EXPOSE 9000
ENV PYTHONUNBUFFERED=1
CMD python /opt/hcx_exporter/main.py
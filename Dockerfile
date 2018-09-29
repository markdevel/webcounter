FROM python:3.6-alpine
COPY requirements.txt /tmp/
RUN apk update \
  && apk add --update --virtual build-dependencies build-base gcc \
  && pip install -r /tmp/requirements.txt \
  && apk del build-dependencies
WORKDIR /opt/webcounter/
COPY src/ /opt/webcounter/
EXPOSE 8000
CMD ["python", "/opt/webcounter/counter.py"]

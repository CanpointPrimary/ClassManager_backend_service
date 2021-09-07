FROM python:3.9-alpine3.13 AS base-py39-alpine310

LABEL maintainer="Canpoint Primary Team<jiangshouming@canpoint.cn>"

WORKDIR /app

COPY /app/requirements.txt /app/
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories && \
    apk add --no-cache --virtual .build-deps gcc libc-dev g++ make py3-numpy py3-pandas py3-cffi py3-lxml py3-psycopg2 libpq postgresql-libs postgresql-dev musl-dev libffi-dev openssl-dev libxml2 libxml2-dev libxslt libxslt-dev\
    && pip install -U pip  \
    && pip install --no-cache-dir -r requirements.txt -i https://pypi.douban.com/simple

RUN pip install --no-cache-dir "uvicorn[standard]" gunicorn -i https://pypi.douban.com/simple

COPY ./scripts/ /
#RUN chmod +x /start.sh && chmod +x /start-reload.sh
RUN chmod +x /start.sh && chmod +x /start-reload.sh

FROM base-py39-alpine310 AS backend

#COPY ./app /app

ENV PYTHONPATH=/app

EXPOSE 80

CMD ["/start.sh"]

FROM base-py39-alpine310 AS celeryworker

#COPY ./app /app

RUN chmod +x /worker-start.sh
ENV PYTHONPATH=/app

CMD ["/worker-start.sh"]

FROM base-py39-alpine310 AS celerybeat

#COPY ./app /app

RUN chmod +x /beat-start.sh
ENV PYTHONPATH=/app

CMD ["/beat-start.sh"]
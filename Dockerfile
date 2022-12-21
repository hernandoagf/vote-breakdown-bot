FROM python:3-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN apk add --no-cache --virtual .build-deps gcc musl-dev git && \ 
pip install --no-cache-dir -r requirements.txt && \ 
apk --purge del .build-deps

COPY ./bot/ /usr/src/app
COPY ./fonts/ /usr/src/app/fonts

CMD [ "python3", "app.py" ]

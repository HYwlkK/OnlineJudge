FROM node:22.14-alpine AS frontend

WORKDIR /frontend

RUN <<EOS
set -ex
apk add --no-cache unzip
wget -O source.zip https://codeload.github.com/QingdaoU/OnlineJudgeFE/zip/refs/tags/oj_2.7.5
echo '22bf2094b175f75e76dda35a89c96004ced36866aa4a62c2b0758a5f3d81870b  source.zip' | sha256sum -c -
unzip -q source.zip
rm -f source.zip
EOS

WORKDIR /frontend/OnlineJudgeFE-oj_2.7.5
RUN npm ci --legacy-peer-deps --ignore-scripts --no-audit --no-fund
COPY frontend/ /overrides/
RUN node /overrides/prepare.js /frontend/OnlineJudgeFE-oj_2.7.5
ENV NODE_OPTIONS=--openssl-legacy-provider
RUN NODE_ENV=production npm run build:dll && npm run build

FROM python:3.12-alpine
ARG TARGETARCH
ARG TARGETVARIANT

ENV OJ_ENV production
WORKDIR /app

COPY ./deploy/requirements.txt /app/deploy/
# psycopg2: libpg-dev
# pillow: libjpeg-turbo-dev zlib-dev freetype-dev
RUN --mount=type=cache,target=/etc/apk/cache,id=apk-cahce-$TARGETARCH$TARGETVARIANT-final \
    --mount=type=cache,target=/root/.cache/pip,id=pip-cahce-$TARGETARCH$TARGETVARIANT-final \
    <<EOS
set -ex
apk add gcc libc-dev python3-dev libpq libpq-dev libjpeg-turbo libjpeg-turbo-dev zlib zlib-dev freetype freetype-dev supervisor openssl nginx curl unzip
pip install -r /app/deploy/requirements.txt
apk del gcc libc-dev python3-dev libpq-dev libjpeg-turbo-dev zlib-dev freetype-dev
EOS

COPY ./ /app/
COPY --from=frontend --link /frontend/OnlineJudgeFE-oj_2.7.5/dist/ /app/dist/
RUN chmod -R u=rwX,go=rX ./ && chmod +x ./deploy/entrypoint.sh

HEALTHCHECK --interval=5s CMD [ "/usr/local/bin/python3", "/app/deploy/health_check.py" ]
EXPOSE 8000
ENTRYPOINT [ "/app/deploy/entrypoint.sh" ]

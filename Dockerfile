FROM ubuntu:26.04

LABEL org.opencontainers.image.title="FollowTheMoney"
LABEL org.opencontainers.image.licenses=MIT
LABEL org.opencontainers.image.source=https://github.com/opensanctions/followthemoney

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -qq -y update \
    && apt-get -qq -y install --no-install-recommends \
        locales ca-certificates tzdata curl \
        python3-pip python3-dev libpq-dev g++ \
        libicu78 libicu-dev icu-devtools pkg-config \
        python3-venv \
    && apt-get -qq -y autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN localedef -i en_US -c -f UTF-8 en_US.UTF-8 \
    && ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && groupadd -g 10023 -r app \
    && useradd -m -u 10023 -s /bin/false -g app app

ENV LANG="en_US.UTF-8" \
    TZ="UTC"

RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN pip3 install -q --no-cache-dir -U pip psycopg2-binary

COPY . /opt/followthemoney
WORKDIR /opt/followthemoney
RUN pip3 install -q --no-cache-dir -e .

USER app
WORKDIR /opt/followthemoney/docs

CMD ["ftm"]

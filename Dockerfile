FROM ubuntu:18.04

RUN mkdir /gpg
RUN mkdir -p /deploy/app 

RUN apt update \
    && apt install -y python-mysqldb libmysqlclient-dev python-dev python-pip libssl-dev mysql-client\
    && rm -rf /var/lib/apt/lists/*

COPY app /deploy/app
WORKDIR /deploy/app
RUN chmod +x entrypoint.sh
RUN pip install -r requirements.txt

ENTRYPOINT [ "/deploy/app/entrypoint.sh" ]

EXPOSE 8000
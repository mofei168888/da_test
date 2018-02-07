FROM daocloud.io/python:3-onbuild

MAINTAINER Robin<robin.chen@b-uxin.com>

ENV LANG C.UTF-8

ENV CATALINA_HOME /usr/local/tomcat

#设置时区,与主机保持一致

RUN /bin/cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo 'Asia/Shanghai' >/etc/timezone


RUN  mkdir -p /app

WORKDIR /app

COPY /app /app
COPY base.txt /app
COPY requirements.txt /app

#安装Python程序运行的依赖库
RUN cd /app && pip install -r base.txt
RUN cd /app && pip install -r requirements.txt


EXPOSE 80


ENTRYPOINT ["python", "/app/zzsd_strategy.py"]
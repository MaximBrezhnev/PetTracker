FROM python:3.11
RUN apt-get update -y
RUN apt-get upgrade -y

WORKDIR /app
COPY . .

RUN fc-cache -f -v
RUN ln -snf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && echo "Europe/Moscow" > /etc/timezone

RUN pip install -r requirements.txt

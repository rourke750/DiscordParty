FROM python:3.10.0-alpine3.14

RUN mkdir -p /home/appuser/houseparty

WORKDIR /home/appuser/houseparty

COPY requirements.txt /home/appuser/houseparty/

RUN python -m pip install -r requirements.txt

COPY ./ /home/appuser/houseparty/

CMD python -m discordparty
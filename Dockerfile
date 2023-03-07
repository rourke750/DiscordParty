FROM python:3.10.0-alpine3.14

RUN mkdir -p /home/appuser/houseparty

COPY ./ /home/appuser/houseparty/

WORKDIR /home/appuser/houseparty

RUN python -m pip install -r requirements.txt

CMD python -m discordparty
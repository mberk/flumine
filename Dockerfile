FROM python:3.6

RUN apt-get -y update

# build flumine
ADD . /flumine
WORKDIR /flumine

# install py libraries
RUN pip install flumine

CMD python main.py $MARKET_FILTER

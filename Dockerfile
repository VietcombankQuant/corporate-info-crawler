FROM python:3.11
COPY __main__.py requirements.txt /corporate-info-crawler/
COPY ./crawler /corporate-info-crawler/crawler
RUN ["python", "-m", "pip", "install", "-r", "/corporate-info-crawler/requirements.txt"]
CMD ["python", "."]
WORKDIR /corporate-info-crawler

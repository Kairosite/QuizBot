FROM python:latest

WORKDIR /CODE

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/ .

CMD [ "python", "./heart.py" ]
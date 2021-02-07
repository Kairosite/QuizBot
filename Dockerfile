# Stage 1
FROM python:latest AS compiler
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"


COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./src /opt/venv


#Stage 2
FROM python:alpine
WORKDIR /opt/venv

COPY --from=compiler /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

CMD [ "python", "heart.py" ]
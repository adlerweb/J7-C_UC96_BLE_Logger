FROM debian:bullseye-slim

RUN apt-get update && apt-get install --yes git python3-gattlib && apt-get clean

COPY j7c.py /j7c.py

ENTRYPOINT ["python3", "/j7c.py"]

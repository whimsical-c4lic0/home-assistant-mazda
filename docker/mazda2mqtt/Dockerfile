FROM debian

WORKDIR /app

RUN apt-get update && apt-get install -y wget unzip python3 python3-venv && \
  python3 -m venv venv && \
  ./venv/bin/python3 -m pip install aiohttp paho-mqtt cryptography python-dotenv

RUN wget https://github.com/brunob45/home-assistant-mazda/archive/refs/heads/mqtt.zip && \
  unzip mqtt.zip && rm -rf mqtt.zip

# COPY .env /app/.env

SHELL ["/bin/ash", "-c"]
CMD ["./venv/bin/python3", "./home-assistant-mazda-mqtt/custom_components/mazda/app.py"]

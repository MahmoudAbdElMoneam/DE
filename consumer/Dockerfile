FROM python:3.10-slim
WORKDIR /usr/local/bin/consumer
COPY . .
RUN pip install -r requirements.txt
CMD ["bokeh", "serve", "--show", "/usr/local/bin/consumer/consumer.py", "--websocket-max-message-size=500000000"]

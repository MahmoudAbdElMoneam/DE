FROM python:3.10-slim
WORKDIR /opt/kafka/config/
RUN echo "bootstrap.servers=kafka1:9093,kafka2:9095,kafka3:9097" >> /opt/kafka/config/host.producer.ssl.config && \
    echo "ssl.keystore.location=/etc/kafka/secrets/kafka.producer.keystore.jks" >> /opt/kafka/config/host.producer.ssl.config && \
    echo "ssl.keystore.password=password" >> /opt/kafka/config/host.producer.ssl.config && \
    echo "ssl.truststore.location=/etc/kafka/secrets/kafka.producer.truststore.jks"  >> /opt/kafka/config/host.producer.ssl.config && \
    echo "ssl.truststore.password=password"  >> /opt/kafka/config/host.producer.ssl.config && \
    echo "ssl.key.password=password"  >> /opt/kafka/config/host.producer.ssl.config && \
    echo "ssl.client.auth=required"  >> /opt/kafka/config/host.producer.ssl.config && \
    echo "ssl.endpoint.identification.algorithm=" >> /opt/kafka/config/host.producer.ssl.config && \
    echo "security.protocol=SASL_SSL"  >> /opt/kafka/config/host.producer.ssl.config && \
    echo "sasl.mechanism=PLAIN"  >> /opt/kafka/config/host.producer.ssl.config && \
    echo "sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required \
    username=\"admin\" \
    password=\"admin-secret\";"  >> /opt/kafka/config/host.producer.ssl.config

WORKDIR /usr/local/bin/producer
COPY . .
RUN pip install -r requirements.txt
CMD [ "python", "./producer.py" ]
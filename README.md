# Data-intensive application for construction costs
This application can be used to collect data from various sources to be shown in a real-time dashboard.

To download it:
$ git clone https://github.com/MahmoudAbdElMoneam/DE

To run it, use cmd to navigate to the folder, then write the following command:
docker-compose -f  docker-compose.yml up

docker will take care of downloading the requirements and starting the containers in order.

When the consumer is ready, you can see the dashboard at:
http://localhost:5006/consumer

We use kafdrop at http://localhost:9000/ https://github.com/obsidiandynamics/kafdrop to monitor kafka topics, brokers, performance, ingested messages, etc.

It is worth mentioning that ensuring data security, governance, and protection of the system can be achieved by securing all our connections, we suggest using SASL_SSL, however there are other methods worth investigating.


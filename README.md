# Data-intensive application for construction costs monitoring
This application can be used to collect data from various sources to be shown in a real-time dashboard.
The system architecture is as follows:

![Screenshot of a software architecture](https://github.com/MahmoudAbdElMoneam/DE/blob/2e1187ecf78deb22f0e4fb358937f292fc752cb5/images/System%20architecture.png)


To clone:
```
git clone https://github.com/MahmoudAbdElMoneam/DE
```

To start the containers in windows, use command prompt to navigate to the folder, then write the following command (or use a similar approach as per the operating system):
```
docker-compose -f docker-compose.yml up
```

docker will take care of downloading the requirements and starting the containers in order.

When the consumer is ready, you can see the dashboard at:
http://localhost:5006/consumer

We use [kafdrop](https://github.com/obsidiandynamics/kafdrop)  at http://localhost:9000/  to monitor kafka topics, brokers, performance, ingested messages, etc.

It is worth mentioning that ensuring data security, governance, and protection of the system can be achieved by securing all our connections, we suggest using SASL_SSL, however there are other methods worth investigating. Moreover, encrypting data in transit and at rest.

This system was developed and tested on windows 10, on a machine with 32 GB of RAM.

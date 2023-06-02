import json
import sys
import time
import json
import random
from datetime import datetime
from kafka import KafkaProducer
import traceback

# exception information
def get_exception_info():
    try:
        exception_type, exception_value, exception_traceback = sys.exc_info()
        file_name, line_number, procedure_name, line_code = traceback.extract_tb(exception_traceback)[-1]
        exception_info = ''.join('[Line Number]: ' + str(line_number) + ' '+ '[Error Message]: ' + str(exception_value) + ' [File Name]: ' + str(file_name) + '\n'+'[Error Type]: ' + str(exception_type) + ' '+' ''[Procedure Name]: ' + str(procedure_name) + ' '+ '[Time Stamp]: '+ str(time.strftime('%d-%m-%Y %I:%M:%S %p'))+ '[Line Code]: ' + str(line_code))
        print(exception_info)
    except:
        pass
    else:
        pass
        # no exceptions occur, run this code
    finally:
        pass
        # code clean-up. this block always executes
    return exception_info

def generate_data(number):
    data_sources = [{"category":"material", "quantity":random.randint(10, 12), "unit_cost": random.randint(3, 5)},
                   {"category":"labor", "quantity":random.randint(3, 5), "unit_cost": random.randint(1, 2)},
                   {"category":"equipment", "quantity":random.randint(1, 3), "unit_cost": random.randint(6, 8)}]
    random.shuffle(data_sources)
    data_sources[0]['timestamp1'] = "{}".format(datetime.utcnow())
    data_sources[0]['number'] = number
    response = data_sources[0]
    return response
# Kafka Producer
# https://kafka-python.readthedocs.io/en/master/apidoc/KafkaProducer.html
if __name__ == '__main__':
    try:
        producer = KafkaProducer(
            # for docker containers connection
            bootstrap_servers=['kafka1:9093', 'kafka2:9095', 'kafka3:9097'],
            # for local debugging
            # bootstrap_servers=['localhost:9092', 'localhost:9094', 'localhost:9096'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8'),
            client_id = 'producer',
            acks = 1,
        )
        total_costs = 0
        for j in range(1000000):
            data = generate_data(j+1)
            # for local debugging to make sure all records appear in the dashboard, actual calculations are made in Spark
            total_costs += data['quantity']*data['unit_cost']
            request = producer.send('ingestion', value=data)
        # for high level debugging of the data
        print(str(j+1) +" records produced, with a total cost of: " + str(total_costs))
        producer.flush()
        producer.close()
    except:
        get_exception_info()




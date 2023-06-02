import sys
import time
import traceback
from pyspark.sql import SparkSession
import pyspark.sql.functions as func
from pyspark.sql.types import *
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


if __name__ == '__main__':
    try:
        CHECKPOINT_LOCATION = '/usr/local/bin/preprocessor/CHECKPOINT'
        spark_version = '3.4.0'
        packages = [f'org.apache.spark:spark-sql-kafka-0-10_2.12:{spark_version}','org.apache.kafka:kafka-clients:{spark_version}']
        spark = SparkSession.builder.appName("preprocessStream") \
        .config("spark.jars.packages", ",".join(packages)) \
        .getOrCreate()
        # Reduce logging
        sc = spark.sparkContext
        sc.setLogLevel("ERROR")
        kafka_bootstrap_servers='kafka1:9093, kafka2:9095, kafka3:9097'
        kafka_output_topic = 'preprocessed'
        # https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html
        kafka_stream = spark.readStream.format("kafka") \
            .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
            .option("subscribe", "ingestion") \
            .option("startingOffsetsByTimestampStrategy", "latest") \
            .option("startingOffsets", "earliest") \
            .load()
        base_df = kafka_stream.selectExpr("CAST(value as STRING)", "timestamp")
        base_df.printSchema()
        data_schema = (StructType()
        .add("category", StringType())
        .add("quantity", IntegerType())
        .add("unit_cost", IntegerType())
        .add("timestamp1", TimestampType())
        .add("number", IntegerType())
        )
        info_dataframe = base_df.select(func.from_json(func.col("value"), data_schema).alias("info"), "timestamp")
        info_df_fin = info_dataframe.select("info.*", "timestamp")
        info_df_fin = info_df_fin.withColumn("total_cost",func.col("unit_cost")*func.col("quantity"))
        # tested these, https://www.databricks.com/blog/2022/08/22/feature-deep-dive-watermarking-apache-spark-structured-streaming.html
        # https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#handling-late-data-and-watermarking
        # https://medium.com/expedia-group-tech/apache-spark-structured-streaming-watermarking-6-of-6-1187542d779f
        aggregatedDF = info_df_fin \
        .groupby(func.col("category")) \
        .agg(func.count("*").alias("count"), \
        func.sum("total_cost").alias("total_cost_alias"), \
        func.last("timestamp1").alias("max_timestamp"))   
        aggregatedDF.printSchema()
        # To output data to a single partition https://stackoverflow.com/questions/56295650/writing-to-multiple-kafka-partitions-from-spark
        result_1 = aggregatedDF.selectExpr(
        "CAST(category AS STRING)",
        "CAST(total_cost_alias AS INT)",
        "CAST(max_timestamp AS TIMESTAMP)",
        "CAST(count AS INT)",
        ).withColumn("value", func.to_json(func.struct("*")).cast("string")) \
        .withColumn("key", func.lit("preprocessed"))
        result = result_1 \
            .select("value", "key") \
            .writeStream \
            .format("kafka") \
            .outputMode("update") \
            .option("topic", kafka_output_topic) \
            .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
            .option("checkpointLocation", CHECKPOINT_LOCATION) \
            .start() \
            .awaitTermination() \
            .trigger(processingTime='1 seconds')
    except:
        get_exception_info()




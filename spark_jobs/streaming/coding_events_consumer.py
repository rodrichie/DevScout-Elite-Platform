"""
Spark Streaming Consumer - Consume and process coding events from Kafka
"""
import os
import logging
from datetime import datetime

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import (
        from_json, col, window, avg, sum as _sum, count, 
        current_timestamp, to_timestamp
    )
    from pyspark.sql.types import (
        StructType, StructField, StringType, IntegerType, 
        FloatType, TimestampType, BooleanType, ArrayType
    )
    HAS_SPARK = True
except ImportError:
    HAS_SPARK = False
    logging.warning("PySpark not installed. Spark streaming disabled.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_spark_session(app_name: str = "CodingEventsConsumer") -> SparkSession:
    """
    Create Spark session with Kafka dependencies.
    
    Args:
        app_name: Application name
        
    Returns:
        SparkSession instance
    """
    spark = SparkSession.builder \
        .appName(app_name) \
        .master("spark://spark-master:7077") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoints") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    logger.info(f" Spark session created: {app_name}")
    
    return spark


def get_event_schema() -> StructType:
    """
    Define schema for coding events.
    
    Returns:
        StructType schema
    """
    return StructType([
        StructField("event_id", StringType(), False),
        StructField("event_type", StringType(), False),
        StructField("candidate_id", IntegerType(), False),
        StructField("challenge_id", StringType(), True),
        StructField("session_id", StringType(), True),
        StructField("timestamp", StringType(), False),
        StructField("tests_passed", IntegerType(), True),
        StructField("tests_total", IntegerType(), True),
        StructField("success_rate", FloatType(), True),
        StructField("execution_time_ms", FloatType(), True),
        StructField("final_score", FloatType(), True),
        StructField("time_taken_seconds", IntegerType(), True),
        StructField("attempts", IntegerType(), True),
        StructField("metric_type", StringType(), True),
        StructField("metric_value", FloatType(), True),
        StructField("errors", ArrayType(StringType()), True),
        StructField("has_errors", BooleanType(), True)
    ])


def consume_coding_events(kafka_bootstrap_servers: str = "kafka:9092",
                         topic: str = "coding-events",
                         postgres_url: str = None):
    """
    Consume coding events from Kafka and process with Spark Streaming.
    
    Args:
        kafka_bootstrap_servers: Kafka broker address
        topic: Kafka topic name
        postgres_url: PostgreSQL JDBC URL for output
    """
    if not HAS_SPARK:
        logger.error(" PySpark not available")
        return
    
    spark = create_spark_session()
    
    # Read from Kafka
    logger.info(f" Subscribing to Kafka topic: {topic}")
    
    kafka_df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
        .option("subscribe", topic) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    # Parse JSON events
    event_schema = get_event_schema()
    
    events_df = kafka_df \
        .selectExpr("CAST(value AS STRING) as json_value") \
        .select(from_json(col("json_value"), event_schema).alias("data")) \
        .select("data.*") \
        .withColumn("processed_at", current_timestamp()) \
        .withColumn("event_timestamp", to_timestamp(col("timestamp")))
    
    # Filter and transform different event types
    
    # 1. Test Results Stream
    test_results_df = events_df \
        .filter(col("event_type") == "test_result") \
        .select(
            col("candidate_id"),
            col("challenge_id"),
            col("tests_passed"),
            col("tests_total"),
            col("success_rate"),
            col("execution_time_ms"),
            col("has_errors"),
            col("event_timestamp")
        )
    
    # Aggregate test results by candidate and challenge (10-minute windows)
    test_aggregates = test_results_df \
        .withWatermark("event_timestamp", "10 minutes") \
        .groupBy(
            window(col("event_timestamp"), "10 minutes"),
            col("candidate_id"),
            col("challenge_id")
        ) \
        .agg(
            avg("success_rate").alias("avg_success_rate"),
            avg("execution_time_ms").alias("avg_execution_time"),
            count("*").alias("attempt_count"),
            _sum("has_errors").alias("error_count")
        )
    
    # 2. Challenge Completions Stream
    completions_df = events_df \
        .filter(col("event_type") == "challenge_completion") \
        .select(
            col("candidate_id"),
            col("challenge_id"),
            col("final_score"),
            col("time_taken_seconds"),
            col("attempts"),
            col("event_timestamp")
        )
    
    # 3. Live Coding Metrics Stream
    live_metrics_df = events_df \
        .filter(col("event_type") == "live_coding_metric") \
        .select(
            col("candidate_id"),
            col("session_id"),
            col("metric_type"),
            col("metric_value"),
            col("event_timestamp")
        )
    
    # Aggregate live metrics by candidate (5-minute windows)
    live_aggregates = live_metrics_df \
        .withWatermark("event_timestamp", "5 minutes") \
        .groupBy(
            window(col("event_timestamp"), "5 minutes"),
            col("candidate_id"),
            col("session_id"),
            col("metric_type")
        ) \
        .agg(
            avg("metric_value").alias("avg_metric_value"),
            count("*").alias("metric_count")
        )
    
    # Write streams to console (for debugging) and PostgreSQL (for persistence)
    
    logger.info(" Starting streaming queries...")
    
    # Console output for test aggregates
    query1 = test_aggregates \
        .writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", "false") \
        .start()
    
    # Console output for completions
    query2 = completions_df \
        .writeStream \
        .outputMode("append") \
        .format("console") \
        .option("truncate", "false") \
        .start()
    
    # Console output for live metrics
    query3 = live_aggregates \
        .writeStream \
        .outputMode("update") \
        .format("console") \
        .option("truncate", "false") \
        .start()
    
    # PostgreSQL output (if URL provided)
    if postgres_url:
        logger.info(" Writing to PostgreSQL...")
        
        # Write completions to database
        query4 = completions_df \
            .writeStream \
            .outputMode("append") \
            .foreachBatch(lambda df, epoch_id: write_to_postgres(
                df, "silver.coding_challenge_scores", postgres_url
            )) \
            .start()
        
        # Wait for all queries
        query1.awaitTermination()
        query2.awaitTermination()
        query3.awaitTermination()
        query4.awaitTermination()
    else:
        # Wait for console queries only
        query1.awaitTermination()
        query2.awaitTermination()
        query3.awaitTermination()


def write_to_postgres(batch_df, table_name: str, jdbc_url: str):
    """
    Write batch DataFrame to PostgreSQL.
    
    Args:
        batch_df: Spark DataFrame
        table_name: Target table name
        jdbc_url: JDBC connection URL
    """
    try:
        batch_df.write \
            .format("jdbc") \
            .option("url", jdbc_url) \
            .option("dbtable", table_name) \
            .option("user", os.getenv("POSTGRES_USER", "airflow")) \
            .option("password", os.getenv("POSTGRES_PASSWORD", "airflow")) \
            .option("driver", "org.postgresql.Driver") \
            .mode("append") \
            .save()
        
        logger.info(f" Batch written to {table_name}: {batch_df.count()} rows")
        
    except Exception as e:
        logger.error(f" Failed to write to PostgreSQL: {e}")


if __name__ == "__main__":
    # Run consumer
    postgres_jdbc = os.getenv(
        "POSTGRES_JDBC_URL",
        "jdbc:postgresql://postgres:5432/devscout"
    )
    
    logger.info(" Starting Spark Streaming Consumer...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        consume_coding_events(
            kafka_bootstrap_servers="kafka:9092",
            topic="coding-events",
            postgres_url=postgres_jdbc
        )
    except KeyboardInterrupt:
        logger.info("\n Consumer stopped by user")
    except Exception as e:
        logger.error(f" Consumer error: {e}")

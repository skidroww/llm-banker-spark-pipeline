import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_replace, avg, count, desc

def main():
    print("🚀 Spark 데이터 파이프라인 시작...")

    # 1. Spark 세션 생성 (Spark의 진입점)
    # local[*]은 내 컴퓨터의 모든 CPU 코어를 사용하여 병렬 처리하겠다는 의미입니다.
    spark = SparkSession.builder \
        .appName("LLMBankerLogAnalytics") \
        .master("local[*]") \
        .getOrCreate()

    # 로그 폴더 경로 (나중에 Docker로 띄울 때는 공유 볼륨 경로로 변경됩니다)
    log_path = "logs/*.jsonl"

    try:
        # 2. JSONL 파일 대량 읽기
        # Spark는 폴더 내의 모든 jsonl 파일을 한 번에 읽어들입니다.
        df = spark.read.json(log_path)
        print("\n📊 [원본 데이터 스키마]")
        df.printSchema()

        # 3. 데이터 전처리 (Flattening)
        # 중첩된 JSON 구조(profile.연령 등)를 평탄화하여 테이블 형태로 만듭니다.
        flat_df = df.select(
            col("session_id"),
            col("timestamp"),
            col("profile.연령").alias("age"),
            col("profile.직업").alias("job"),
            col("profile.결혼상태").alias("marital_status"),
            col("profile.연간평균잔고").alias("balance"),
            col("profile.예치성향점수").alias("deposit_prob_str"),
            col("chat.question").alias("question")
        )

        # '59.7%' 처럼 문자열로 된 예치성향점수에서 '%'를 떼어내고 실수(Float)로 변환
        processed_df = flat_df.withColumn(
            "deposit_prob",
            regexp_replace(col("deposit_prob_str"), "%", "").cast("float")
        )

        print("\n👀 [전처리된 데이터 미리보기]")
        processed_df.show(5, truncate=False)

        # 4. 데이터 집계 (Aggregation) 
        # 예시 분석: "직업 및 결혼 상태별 평균 예치 성향과 질문 수"
        stats_df = processed_df.groupBy("job", "marital_status").agg(
            count("session_id").alias("total_chats"),
            avg("balance").alias("avg_balance"),
            avg("deposit_prob").alias("avg_deposit_prob")
        ).orderBy(desc("total_chats"))

        print("\n📈 [분석 결과: 직업/결혼상태별 통계]")
        stats_df.show()

        # 5. 결과물 저장 (Data Ingestion)
        # 분석된 결과를 다른 시스템이 볼 수 있도록 CSV로 내보냅니다.
        output_dir = "output/user_stats"
        print(f"\n💾 분석 결과를 '{output_dir}' 폴더에 CSV 형식으로 저장합니다...")
        
        # coalesce(1)은 분산된 파티션을 1개의 파일로 합쳐서 저장하라는 의미입니다.
        stats_df.coalesce(1) \
            .write \
            .mode("overwrite") \
            .option("header", "true") \
            .csv(output_dir)
            
        print("✅ Spark 파이프라인 작업 완료!")

    except Exception as e:
        print(f"❌ 데이터 처리 중 오류 발생: {e}")
    finally:
        # Spark 세션 종료 (메모리 반환)
        spark.stop()

if __name__ == "__main__":
    main()
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_replace, avg, count, desc
from pyspark.sql import functions as F
from pyspark.sql.types import FloatType

def save_to_csv(df, folder_name):
    """DataFrame을 지정된 폴더에 1개의 CSV 파일로 덮어쓰기 저장하는 헬퍼 함수"""
    output_path = f"output/{folder_name}"
    df.coalesce(1).write.mode("overwrite").option("header", "true").csv(output_path)
    print(f"  └─ 📁 저장 완료: {output_path}")

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
        # 1.데이터 로드
        df = spark.read.json(log_path)
        if df.rdd.isEmpty():
            print("⚠️ 처리할 로그 데이터가 없습니다.")
            return
        
        print("\n📊 [원본 데이터 스키마]")
        df.printSchema()

        # 2. 데이터 전처리 (Flattening & Type Casting)
        # 시간, 프로필, 채팅 내용을 평탄화하고 필요한 타입으로 변환합니다.
        processed_df = df.select(
            F.col("session_id"),
            F.to_timestamp(F.col("timestamp")).alias("timestamp"),
            F.col("profile.연령").cast("int").alias("age"),
            F.col("profile.직업").alias("job"),
            F.col("profile.결혼상태").alias("marital_status"),
            F.col("profile.연간평균잔고").cast("long").alias("balance"),
            F.col("profile.주택담보대출여부").alias("housing_loan"),
            F.col("profile.개인신용대출여부").alias("personal_loan"),
            F.regexp_replace(F.col("profile.예치성향점수"), "%", "").cast("float").alias("deposit_prob"),
            F.col("chat.question").alias("question")
        )

        # 파생 변수 생성: 나이를 10단위로 묶어 '연령대(age_group)' 생성 (예: 54 -> 50대)
        # 파생 변수 생성: 날짜(date)와 시간(hour) 추출
        processed_df = processed_df \
            .withColumn("age_group", F.concat((F.floor(F.col("age") / 10) * 10).cast("int"), F.lit("대"))) \
            .withColumn("date", F.to_date(F.col("timestamp"))) \
            .withColumn("hour", F.hour(F.col("timestamp")))

        print("\n📊 데이터 마트(Data Mart) 생성 및 CSV 추출 중...")


        print("\n👀 [전처리된 데이터 미리보기]")
        processed_df.show(20, truncate=False)

        # ==========================================
        # 💡 [섹션 1] 핵심 KPI 분석
        # ==========================================
        kpi_df = processed_df.agg(
            F.count("session_id").alias("total_chats"),
            F.countDistinct("session_id").alias("total_unique_users"),
            F.round(F.avg("deposit_prob"), 2).alias("avg_deposit_prob")
        ).withColumn(
            "avg_chats_per_user", 
            F.round(F.col("total_chats") / F.col("total_unique_users"), 2)
        )
        save_to_csv(kpi_df, "kpi_summary")

        # ==========================================
        # 💡 [섹션 2] 인구통계학적 분석 (Demographics)
        # ==========================================
        # 2-1. 연령대별 분포
        age_dist_df = processed_df.groupBy("age_group").count().orderBy("age_group")
        save_to_csv(age_dist_df, "demographics_age")

        # 2-2. 직업별 분포
        job_dist_df = processed_df.groupBy("job").count().orderBy(F.desc("count"))
        save_to_csv(job_dist_df, "demographics_job")

        # 2-3. 대출 보유 현황 분석 (주택담보, 개인신용)
        loan_dist_df = processed_df.groupBy("housing_loan", "personal_loan").count()
        save_to_csv(loan_dist_df, "demographics_loan")

        # ==========================================
        # 💡 [섹션 3] 심층 교차 분석 (Cross-Analysis)
        # ==========================================
        # 3-1. 시간대별 채팅 트렌드
        time_trend_df = processed_df.groupBy("date", "hour").count().orderBy("date", "hour")
        save_to_csv(time_trend_df, "trend_time")

        # 3-2. 연령대별 평균 자산(잔고)
        wealth_by_age_df = processed_df.groupBy("age_group").agg(
            F.round(F.avg("balance"), 0).alias("avg_balance")
        ).orderBy("age_group")
        save_to_csv(wealth_by_age_df, "wealth_by_age")

        # 3-3. 많이 묻는 질문 키워드 (Word Cloud용)
        # 질문 텍스트를 공백 기준으로 쪼개고, 2글자 이상인 단어만 추출하여 빈도수 계산
        words_df = processed_df.select(F.explode(F.split(F.col("question"), "\\s+")).alias("word"))
        keyword_df = words_df.filter(F.length(F.col("word")) >= 2) \
            .groupBy("word").count() \
            .orderBy(F.desc("count")).limit(50)
        save_to_csv(keyword_df, "keywords_top50")

        print("\n✅ [성공] 10가지 통계 지표가 모두 output 폴더에 저장되었습니다!")

    except Exception as e:
        print(f"❌ 데이터 처리 중 오류 발생: {e}")
    finally:
        # Spark 세션 종료 (메모리 반환)
        spark.stop()

if __name__ == "__main__":
    main()
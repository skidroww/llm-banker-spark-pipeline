# FinRAG Spark Data Pipeline & Admin Dashboard

본 프로젝트는 [LLM Banker RAG Chatbot](https://github.com/skidroww/llm-banker-rag-chatbot)에서 생성되는 대규모 사용자 대화 로그를 처리하고 시각화하는 **빅데이터 파이프라인 및 비즈니스 인텔리전스(BI) 대시보드**입니다.
> 제작 기간: 2026.03.21. ~ 2026.03.23.

분산 파일 시스템 환경을 가정하여 일일 단위로 쌓이는 대량의 JSONL 로그 파일을 **Apache Spark**로 병렬 처리합니다. 가공된 데이터는 여러 개의 데이터 마트(Data Mart)로 분리 저장되며, **Streamlit** 기반의 관리자 대시보드에서 실시간 통계 차트로 시각화됩니다.

## Key Features(주요 기능)

* **Big Data Processing (Apache Spark)**
  * 대용량 JSONL 비정형 로그 데이터를 분산/병렬 처리하여 데이터 전처리 및 타입 캐스팅 수행.
  * 자연어 텍스트 분리(NLP 전처리), 파생 변수(연령대, 시간대) 생성 로직 구현.
* **Real-time BI Dashboard (Streamlit & Plotly)**
  * Spark가 분석한 결과물(CSV)을 읽어와 화면 스크롤 없이 한눈에 들어오는 관제 대시보드 구축.
  * KPI 요약, 인구통계학적 파이/바 차트, 시계열 트렌드, 검색어 워드클라우드 등 제공.
* **MSA(Microservices Architecture) & Docker**
  * 데이터 처리부(`spark_worker`)와 시각화부(`admin_dashboard`)를 별도의 컨테이너로 분리.
  * `docker-compose`의 Bind Mount를 활용해 챗봇 서버와 로그 데이터를 공유하는 결합도 낮은 아키텍처 설계.
* **1M+ Dummy Data Generator**
  * 빅데이터 처리 성능 검증을 위해 현실적인 가중치(연령별 관심사, 직업, 대출 보유 여부 등)가 적용된 100만 건 이상의 더미 로그 생성 스크립트 포함.
  * PySpark 분산 처리를 통해 100만 건 이상의 대규모 로그 데이터도 빠르고 안정적으로 처리.

---
## Tech Stack(기술 스택)
* **Language**: Python 3.10
* **Data Processing**: Apache Spark (PySpark 3.5.1), Pandas 2.2.1
* **Dashboard / UI**: Streamlit 1.55.0, Plotly 6.6.0
* **Infrastructure**: Docker, Docker Compose
* **Data Format**: JSONL (Input), CSV (Output Data Mart)
---

## Architecture & Data Flow

이 파이프라인은 다음과 같은 흐름으로 작동합니다.

1. **Log Generation:** 챗봇 컨테이너가 사용자의 채팅 로그를 `logs/` 볼륨에 JSONL 형태로 쌓습니다. (또는 `generate_dummy_logs.py`로 대용량 데이터 모의 생성)
2. **Batch Processing:** `spark_worker` 컨테이너가 60초(사용자 정의) 주기로 깨어나 신규 로그를 읽고, 10가지 인사이트 통계(Data Mart)를 계산하여 `output/` 폴더에 CSV로 덮어씁니다.
3. **Data Visualization:** `admin_dashboard` 컨테이너가 갱신된 데이터를 감지하고, 관리자가 접속 시 최신 차트를 웹 화면에 렌더링합니다.

---

## 분석 인사이트 (Data Marts)

Spark 파이프라인을 통해 총 3가지 섹션, 10개의 핵심 지표를 추출합니다.

1. **핵심 KPI:** 총 누적 대화 수, 고유 사용자 수(Sessions), 세션당 평균 대화 턴 수, 전체 고객 평균 예치 성향
2. **인구통계 교차 분석:** 연령대별 분포, 직업별 분포, 연령대별 평균 자산(잔고), 고객 대출 보유 현황(주택담보/신용)
3. **트렌드 및 NLP 분석:** 시간대별 챗봇 접속 트렌드, 자주 묻는 질문 키워드 추출(Top 10)

---

## Project Structure

```text
llm-banker-spark-pipeline/
├── spark_processor.py         # Apache Spark 로그 분석 및 CSV 변환 스크립트
├── admin_dashboard.py         # Streamlit 기반 실시간 관리자 대시보드 UI
├── generate_dummy_logs.py     # 대용량 테스트용 100만 건 더미 로그 생성 스크립트
├── Dockerfile                 # Spark 및 Python 환경 구축 레시피
├── docker-compose.yml         # Worker 및 Dashboard 다중 컨테이너 오케스트레이션
├── requirements.txt           # Python 의존성 패키지 목록
├── logs/                      # 원본 JSONL 챗봇 로그 보관함
└── output/                    # Spark 분석 결과물이 저장되는 Data Mart 폴더 (CSV)
```
---

## Getting Started (실행 방법)
1. 사전 준비 (대용량 더미 데이터 생성)
Spark의 대규모 분산 처리 성능을 확인하기 위해, 약 100만 건의 더미 로그 데이터를 먼저 생성합니다.

Bash
python generate_dummy_logs.py
(실행 완료 후 logs/dummy_chat_logs.jsonl 파일이 약 300MB 크기로 생성됩니다.)

2. Docker Compose로 파이프라인 & 대시보드 실행
의존성 문제 없이 Docker를 통해 스파크 워커와 대시보드 서버를 한 번에 띄웁니다.

Bash
docker-compose up -d --build
3. 결과 확인
Spark Worker: 백그라운드에서 60초 주기로 빅데이터를 분석하여 output/ 폴더를 갱신합니다.

Admin Dashboard: 웹 브라우저를 열고 http://localhost:8502 에 접속하여 실시간으로 업데이트되는 화려한 관제 화면을 확인하세요

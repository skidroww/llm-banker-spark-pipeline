# LLM Banker Spark Pipeline 🚀

이 프로젝트는 [LLM Banker RAG Chatbot](기존 레포 링크)에서 발생하는 대규모 사용자 대화 로그와 프로필 정보를 처리하기 위한 **Apache Spark 기반의 데이터 분석 파이프라인**입니다.

기존 데이터베이스에 의존하지 않고, 분산 파일 시스템 환경을 가정하여 일일 단위로 쌓이는 대량의 JSONL 로그 파일을 병렬로 읽고 분석합니다. 이를 통해 연령대별 금융 상품 관심도, 대출 여부에 따른 주요 질문 트렌드 등의 인사이트를 추출합니다. 

**Key Features:**
* DB-less Architecture (공유 볼륨 기반의 JSONL 파일 처리)
* PySpark를 활용한 대용량 로그 병렬 분산 처리
* 사용자 프로필(나이, 대출 여부 등)과 채팅 내역 교차 분석
* Docker & Docker Compose를 통한 MSA(Microservices Architecture) 환경 구축
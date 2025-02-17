# models/research.py

import logging
from datetime import date
from dataclasses import dataclass, field
from typing import Optional, List, Callable

import psycopg2
from psycopg2 import extensions

# 외부에서 제공하는 DB 커넥션 생성 함수
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection


@dataclass
class Research:
    """
    Research 데이터 모델.
    id는 DB에서 자동 생성되므로 기본값은 None으로 처리합니다.
    """
    research_name: str
    research_key: str
    manager: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[int] = None
    status: str = "in_progress"
    description: Optional[str] = None
    id: Optional[int] = field(default=None)

    @classmethod
    def from_row(cls, row: tuple) -> "Research":
        """
        DB에서 조회한 튜플을 Research 인스턴스로 변환합니다.
        컬럼 순서는: id, research_name, research_key, manager, start_date, end_date, budget, status, description
        """
        return cls(
            id=row[0],
            research_name=row[1],
            research_key=row[2],
            manager=row[3],
            start_date=row[4],
            end_date=row[5],
            budget=row[6],
            status=row[7],
            description=row[8]
        )


class ResearchRepository:
    """
    Research 관련 DB CRUD 작업을 담당하는 Repository 클래스.
    
    DB 커넥션 생성은 의존성 주입(Dependency Injection) 방식으로 처리합니다.
    """
    def __init__(self, connection_factory: Callable[[], extensions.connection] = get_connection):
        """
        :param connection_factory: DB 커넥션을 반환하는 함수 (기본값은 get_connection)
        """
        self.connection_factory = connection_factory

    def create_table(self) -> None:
        """research 테이블을 생성합니다."""
        logging.info("Creating research table...")
        query = """
            CREATE TABLE IF NOT EXISTS research (
                id SERIAL PRIMARY KEY,
                research_name TEXT NOT NULL,
                research_key TEXT UNIQUE,
                manager TEXT NOT NULL,
                start_date DATE,
                end_date DATE,
                budget INT,
                status TEXT,
                description TEXT
            );
        """
        try:
            with self.connection_factory() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            logging.error("Error creating research table: %s", e)
            raise

    def drop_table(self) -> None:
        """research 테이블이 존재하면 삭제합니다."""
        logging.info("Dropping research table if exists...")
        query = "DROP TABLE IF EXISTS research;"
        try:
            with self.connection_factory() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                conn.commit()
        except psycopg2.Error as e:
            logging.error("Error dropping research table: %s", e)
            raise

    def insert(self, research: Research) -> int:
        """
        Research 레코드를 DB에 삽입합니다.
        
        :param research: 삽입할 Research 객체 (id는 None)
        :return: 새로 생성된 레코드의 id
        """
        query = """
            INSERT INTO research (research_name, research_key, manager, start_date, end_date, budget, status, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        params = (
            research.research_name,
            research.research_key,
            research.manager,
            research.start_date,
            research.end_date,
            research.budget,
            research.status,
            research.description
        )
        try:
            with self.connection_factory() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    new_id = cur.fetchone()[0]
                conn.commit()
            research.id = new_id
            return new_id
        except psycopg2.Error as e:
            logging.error("Error inserting research record: %s", e)
            raise

    def get_by_id(self, research_id: int) -> Optional[Research]:
        """
        id를 기반으로 Research 레코드를 조회합니다.
        
        :param research_id: 조회할 Research의 id
        :return: Research 객체 또는 None
        """
        query = """
            SELECT id, research_name, research_key, manager, start_date, end_date, budget, status, description
            FROM research
            WHERE id = %s;
        """
        try:
            with self.connection_factory() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (research_id,))
                    row = cur.fetchone()
            return Research.from_row(row) if row else None
        except psycopg2.Error as e:
            logging.error("Error fetching research by id %s: %s", research_id, e)
            raise

    def get_by_key(self, research_key: str) -> Optional[Research]:
        """
        research_key를 기반으로 Research 레코드를 조회합니다.
        
        :param research_key: 조회할 research_key 값
        :return: Research 객체 또는 None
        """
        query = """
            SELECT id, research_name, research_key, manager, start_date, end_date, budget, status, description
            FROM research
            WHERE research_key = %s;
        """
        try:
            with self.connection_factory() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (research_key,))
                    row = cur.fetchone()
            return Research.from_row(row) if row else None
        except psycopg2.Error as e:
            logging.error("Error fetching research by key %s: %s", research_key, e)
            raise

    def get_all(self) -> List[Research]:
        """
        모든 Research 레코드를 조회합니다.
        
        :return: Research 객체 리스트
        """
        query = """
            SELECT id, research_name, research_key, manager, start_date, end_date, budget, status, description
            FROM research
            ORDER BY id;
        """
        try:
            with self.connection_factory() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    rows = cur.fetchall()
            return [Research.from_row(row) for row in rows]
        except psycopg2.Error as e:
            logging.error("Error fetching all research records: %s", e)
            raise


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # devcontainer 환경 등에서 sys.path 디버깅
    import sys, os
    logging.info("sys.path: %s", sys.path)
    
    # ResearchRepository 인스턴스 생성 (get_connection 주입)
    repo = ResearchRepository()
    
    # 테스트를 위해 기존 테이블 삭제 후 재생성
    repo.drop_table()
    repo.create_table()
    
    # 새 연구과제 레코드 생성 (id는 DB에서 생성)
    research_record = Research(
        research_name="배터리/ESS/전기자동차 화재 확산과 피해 예측을 위한 인공지능 응용형 시뮬레이션 프로그램 개발",
        research_key="RS-2023-00217016",
        manager="김지태",
        start_date=date(2023, 4, 1),
        end_date=date(2027, 3, 31),
        budget=0,
        status="in_progress",
        description=""
    )
    
    new_id = repo.insert(research_record)
    logging.info("Inserted Research ID: %s", new_id)
    
    # research_key로 레코드 조회
    fetched_record = repo.get_by_key("RS-2023-00217016")
    if fetched_record:
        logging.info("Fetched Research: %s", fetched_record)
    else:
        logging.info("No research found with the given key.")

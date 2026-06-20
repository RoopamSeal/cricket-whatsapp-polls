"""
PostgreSQL Database operations with Connection Pooling
"""
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import streamlit as st
import uuid
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class Database:
    """Wrapper for PostgreSQL operations using a Connection Pool"""
    
    def __init__(self):
        """Initialize connection pool using Streamlit Secrets"""
        self.db_url = st.secrets["database"]["URL"]
        try:
            # Create a pool of 1 to 10 connections
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10, self.db_url
            )
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    def _get_connection(self):
        """Get a connection from the pool"""
        return self.connection_pool.getconn()

    def _put_connection(self, conn):
        """Return a connection to the pool"""
        self.connection_pool.putconn(conn)

    def _convert_query(self, query: str) -> str:
        """Converts SQL placeholders to PostgreSQL %s format"""
        return query.replace('?', '%s')

    def execute(self, query: str, params: tuple = ()) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(self._convert_query(query), params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Execute error on query [{query}]: {e}")
            return False
        finally:
            self._put_connection(conn)

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(self._convert_query(query), params)
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Fetch_one error on query [{query}]: {e}")
            return None
        finally:
            self._put_connection(conn)

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(self._convert_query(query), params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Fetch_all error on query [{query}]: {e}")
            return []
        finally:
            self._put_connection(conn)

    def insert(self, table: str, data: Dict[str, Any]) -> Optional[str]:
        conn = self._get_connection()
        try:
            record_id = data.get(f"{table[:-1]}_id") or data.get('id') or str(uuid.uuid4())
            data[f"{table[:-1]}_id"] = record_id  # Ensure ID is in data
            
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            values = tuple(data.values())
            
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            with conn.cursor() as cursor:
                cursor.execute(query, values)
            conn.commit()
            return record_id
        except Exception as e:
            conn.rollback()
            logger.error(f"Insert error in table [{table}]: {e}")
            return None
        finally:
            self._put_connection(conn)

    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple = ()) -> bool:
        conn = self._get_connection()
        try:
            set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
            values = tuple(data.values()) + where_params
            query = f"UPDATE {table} SET {set_clause} WHERE {self._convert_query(where)}"
            
            with conn.cursor() as cursor:
                cursor.execute(query, values)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Update error in table [{table}]: {e}")
            return False
        finally:
            self._put_connection(conn)

    def count(self, table: str, where: str = "", where_params: tuple = ()) -> int:
        query = f"SELECT COUNT(*) as count FROM {table}"
        if where:
            query += f" WHERE {self._convert_query(where)}"
        result = self.fetch_one(query, where_params)
        return result['count'] if result else 0

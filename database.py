from typing import (
    List,
    Dict,
    Optional,
)
import pandas as pd
import sqllite
import logging

logger = logging.getLogger(__name__)



import sqlite3
import pandas as pd


class SQLLite():
    

    def __init__(self, db_path=None):
        
        if db_path is None:
            db_path = "databases/sample_data/chinook.sqlite"
        self.db_path = db_path

    def get_cursor(self) -> sqlite3.Cursor:
    
        if "db" not in g:
            g.db = sqlite3.connect(self.db_path)
            g.cursor = g.db.cursor()
        return g.cursor

    def close_connection(self) -> None:
        """Disconnect from SQLLite"""
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def run_query(self, query: str) -> pd.DataFrame:
        
        if "db" not in g:
            self.get_cursor()
        return pd.read_sql_query(query, g.db)

    def get_tables(self) -> pd.DataFrame:
        return self.run_query(
            "select name as table_name from sqlite_master where type='table'"
        )

    def get_schema(self, table_name: str):
        
        return self.run_query(f"PRAGMA table_info({table_name})")


class SampleDataCatalog():
    
    def __init__(self, llm):
      
        self.llm = llm
        self.db = SQLLite()

    def _get_all_tables(self) -> pd.DataFrame:
       
        df_path = "/databases/sample_data/chinook_tables.csv"
        return pd.read_csv(df_path)

    def _get_table_schema(self, table_name: str) -> pd.DataFrame:
       
        return self.db.get_schema(table_name)

    def get_source_tables(self, question: str) -> List[Optional[Table]]:
       
        tables_df = self._get_all_tables()
        logger.info(f"Question: {question}")

        response = self.llm.get_reply(
            system_prompt=system_prompt,
            prompt=render_source_tables_prompt(question, tables_df),
        )

        table_list: List[Optional[Table]] = []

        if response.lower().strip() == "no tables found":
            return table_list
        else:
            tables = [tbl.strip() for tbl in response.split(",")]
            logger.info(f"Tables: {tables}")
            logger.info(
                f"Length of tables DF: {len(tables_df[tables_df.table_name.isin(tables)])}"
            )
            logger.info(
                f"Length of tables DF: {len(tables_df[tables_df.table_name.isin(tables)])}"
            )

            for _, row in tables_df[tables_df.table_name.isin(tables)].iterrows():
                table_list.append(
                    Table(name=row.table_name, description=row.description)
                )

            return table_list

    def get_table_schemas(self, table_list: List[str]) -> Dict[str, pd.DataFrame]:
        
        result = {}
        for table in table_list:
            result[table] = self._get_table_schema(table)

        return result
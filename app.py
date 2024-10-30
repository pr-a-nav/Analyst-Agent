import pandas as pd
import loggger
import typing




class AutoAnalyst:

    def __init__(
        self,
        database: BaseDatabase,
        datacatalog: BaseDataCatalog,
        driver_llm: BaseLLM,
        query_retry_count: int = 0,
    ) -> None:
        self.database = database
        self.datacatalog = datacatalog
        self.driver_llm = driver_llm
        # self.analysis: Optional[Analysis] = None
        # self.query: Optional[str] = None
        # self.query_prompt: Optional[str] = None
        self.query_retry_count = query_retry_count
        logger.info(
            f"Initalized AutoAnalyst with retry count: {self.query_retry_count}"
        )
  
  
    def analyze(self, question: str) -> Analysis:

        analysis = Analysis(question)
        logger.info(f"Analyzing question: {question}")

        analysis_type = self.driver_llm.get_reply(
            messages=render_type_messages(question)
        )  # type: ignore
        logger.info(f"Analysis type: {analysis_type}")

        analysis.analysis_type = AnalysisType(analysis_type)

        # Determine source data
        source_tables = self.datacatalog.get_source_tables(question)
        if len(source_tables) == 0:
            raise ValueError("No source tables found")

        analysis.metadata = {"source_data": [tbl.to_str() for tbl in source_tables]}  # type: ignore
        logger.info(f"Source tables: {[tbl.to_str() for tbl in source_tables]}")  # type: ignore

        table_schema = self.datacatalog.get_table_schemas([tbl.name for tbl in source_tables])  # type: ignore
        analysis.metadata = {"table_schema": {k: v.to_dict(orient="records") for k, v in table_schema.items()}}  # type: ignore
        logger.info(f"Table schema: {table_schema}")

        if analysis_type in ["query", "data"]:
            # Generate query
            query_prompt, query = self._generate_data_query(
                question=question,
                source_data=source_tables,  # type: ignore
                table_schema=table_schema,
                analysis_type=analysis_type,
            )
            analysis.query = query

        if analysis_type == "data":
            # Run query
            result_data = self._run_query(
                query=query,
                query_prompt=query_prompt,
                retry_count=self.query_retry_count,
            )
            analysis.result_data = result_data
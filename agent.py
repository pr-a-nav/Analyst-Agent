import typing
import pandas as pd
import logger

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

    def _generate_data_query(
        self,
        question: str,
        source_data: typing.List[Table],
        table_schema: typing.Dict,
        analysis_type: str,
        transformed_data: str = "",
    ) -> typing.Tuple[str, str]:
        """Generate query to answer the question"""
        query_prompt = render_query_prompt(
            question=question,
            source_data=source_data,
            table_schema=table_schema,
            analysis_type=analysis_type,
            transformed_data=transformed_data,
        )
        logger.info(f"Query prompt: {query_prompt}")
        query = self.driver_llm.get_code(
            prompt=query_prompt,
            system_prompt=query_system_prompt,
        )

        return query_prompt, query
    
    def _update_query(self, query: str, query_prompt: str, error: str) -> str:
        """Update query to answer the question"""

        update_query_prompt = render_update_query_prompt(
            prompt=query_prompt,
            query=query,
            error=error,
        )
        logger.info(f"Update query prompt: {update_query_prompt}")
        query = self.driver_llm.get_code(
            prompt=update_query_prompt,
            system_prompt=query_system_prompt,
        )
        logger.info(f"Updated query: {query}")
        return query  # Type: ignore

    def _run_query(
        self, query: str, query_prompt: str, retry_count: int = 0
    ) -> pd.DataFrame:
        """Run query and return the result"""
        try:
            return self.database.run_query(query)
        except Exception as e:
            if retry_count > 0:
                query = self._update_query(
                    query=query, query_prompt=query_prompt, error=str(e)
                )
                return self._run_query(
                    query=query, query_prompt=query_prompt, retry_count=retry_count - 1
                )
from typing import Union, List, Tuple, Dict
import string
import Llm




class Engine :

    def __init__(self,
                  data_source : str,
                  llm_name : str) -> None:
        self.data_source = data_source
        self.llm =llm_name
    
    def data_query (self, llm, user_prompt: string):
        query :str = Llm.Basellm.generatecode()
        return query
import re
from query_db import search_by_shorturl

code = """

    from enum import Enum
    from typing import ClassVar
    
    from .azure_ai_search import AzureAISearch
    from .lancedb import LanceDBVectorStore
    
    
    class VectorStoreType(str, Enum):
    
        LanceDB = "lancedb"
        AzureAISearch = "azure_ai_search"
    """

def local_search(table, directory, code):
    pattern = re.compile(r'from \.(\w+) import (\w+)')
    result = {}
    context = ""

    matches = pattern.findall(code)

    for file, module in matches:
        file = directory + "/" + file + ".py"
        result[file] = module

    for i in result.keys():
        file = search_by_shorturl(table, i)
        context += f"Context for {file[2]} \n\n" + file[3] + "\n"
    return context

directory = "vector_stores"
table = "microsoft_graphrag"

"""
context = local_search(table, directory, code)

print(context)
"""
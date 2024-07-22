# config.py
class Config:
    DATABASES = ["yago", "db2", "db3"]  # 添加你的数据库选项

# 其他配置项



query_prompt = {
    "yago":{
        "type": "knowledge graph",
        "label": "rdfs__label, rdfs__comment",
        "example":"if the natural language query is 'What's basketball', the Cypher query should be like '```MATCH (n)-[r]-(neighbor) WHERE n.rdfs__label CONTAINS 'Basketball' RETURN n, r, neighbor LIMIT 25```'"

    }
}
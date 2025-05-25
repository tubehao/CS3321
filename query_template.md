1. 查询任意一个作者与其写的所有论文
```
MATCH (a:Author)-[:AUTHORS]->(p:Paper)
WHERE a.name = "Yann LeCun"
WITH a, p
LIMIT 20
RETURN
collect(DISTINCT {id: a.author_id, label: a.name}) +
collect(DISTINCT {id: p.publication_id, label: p.title}) AS nodes,
collect(DISTINCT {source: a.author_id, target: p.publication_id, label: 'AUTHORS'}) AS edges
```

2. 查询合作次数最多的前 10 位作者与主作者的关系
```
MATCH (a:Author)-[:AUTHORS]->(p:Paper)<-[:AUTHORS]-(co:Author)
WHERE a.name = "Yann LeCun" AND a.author_id <> co.author_id
WITH co, count(p) AS collaborations
ORDER BY collaborations DESC
LIMIT 10

MATCH (co)-[:AUTHORS]->(p:Paper)<-[:AUTHORS]-(a:Author)
WHERE a.name = "Yann LeCun"
RETURN 
collect(DISTINCT {id: a.author_id, label: a.name}) +
collect(DISTINCT {id: co.author_id, label: co.name}) AS nodes,
collect(DISTINCT {source: a.author_id, target: co.author_id, label: 'CO_AUTHOR'}) AS edges
```

3. 查询全图中的一部分
```
MATCH (a:Author)-[:AUTHORS]->(p:Paper)
WITH a, p
LIMIT 10
RETURN
collect(DISTINCT {id: toString(a.author_id), label: a.name}) +
collect(DISTINCT {id: p.publication_id, label: p.title}) AS nodes,
collect(DISTINCT {source: toString(a.author_id), target: p.publication_id, label: 'AUTHORS'}) AS edges
```

4. 插入Author
```
CREATE (:Author {author_id: 'test_author_001', name: 'Test Author'})
```

5. 插入Paper
```
CREATE (:Paper {publication_id: 'test_paper_001', title: 'Test Paper', year: 2025})
```

6. 插入AUTHOR关系
```
MERGE (a:Author {author_id: 'test_author_001'})
MERGE (p:Paper {publication_id: 'test_paper_001'})
MERGE (a)-[:AUTHORS]->(p)
```
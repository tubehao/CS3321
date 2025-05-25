1. 查询作者+论文
```
MATCH (a:Author)-[:AUTHORS]->(p:Paper)
WHERE a.name = "Jie Guo"
WITH a, p
LIMIT 20
RETURN
collect(DISTINCT {id: a.author_id, label: a.name, ntype: 'author'}) +
collect(DISTINCT {id: p.publication_id, label: p.title, ntype: 'publication'}) AS nodes,
collect(DISTINCT {source: a.author_id, target: p.publication_id, label: 'AUTHORS'}) AS edges
```

2. 查询作者+论文+合作者
```
MATCH (a:Author)-[:AUTHORS]->(p:Paper)
WHERE a.name = "Jie Guo"
WITH a, p
LIMIT 10

MATCH (p)<-[:AUTHORS]-(co:Author)
WITH a, p, co

RETURN
collect(DISTINCT {id: a.author_id, label: a.name, ntype: 'author'}) +
collect(DISTINCT {id: co.author_id, label: co.name, ntype: 'author'}) +
collect(DISTINCT {id: p.publication_id, label: p.title, ntype: 'publication'}) AS nodes,
collect(DISTINCT {source: a.author_id, target: p.publication_id, label: 'AUTHORS'}) +
collect(DISTINCT {source: co.author_id, target: p.publication_id, label: 'AUTHORS'}) AS edges
```

<!-- 3. 查询发表论文最多的top 3作者
```
MATCH (a:Author)-[:AUTHORS]->(p:Paper)
WITH a, count(p) AS paperCount
ORDER BY paperCount DESC
LIMIT 3

MATCH (a)-[:AUTHORS]->(p:Paper)
WITH a, collect(p)[0..10] AS papers

UNWIND papers AS p

RETURN
collect(DISTINCT {id: a.author_id, label: a.name, ntype: "author"}) +
collect(DISTINCT {id: p.publication_id, label: p.title, ntype: "publication"}) AS nodes,
collect(DISTINCT {source: a.author_id, target: p.publication_id, label: "AUTHORS"}) AS edges
``` -->

4. 插入Author, Paper, AUTHOR关系
```
MERGE (a:Author {author_id: 'test_author_001'})
  ON CREATE SET a.name = 'Test Author'

MERGE (p:Paper {publication_id: 'test_paper_001'})
  ON CREATE SET p.title = 'Test Paper'

MERGE (a)-[:AUTHORS]->(p)
```

5. 查询新插入的节点和关系
```
MATCH (a:Author)-[:AUTHORS]->(p:Paper)
WHERE a.author_id STARTS WITH 'test_' AND p.publication_id STARTS WITH 'test_'
RETURN
collect(DISTINCT {id: a.author_id, label: a.name, ntype: 'author'}) + 
collect(DISTINCT {id: p.publication_id, label: p.title, ntype: 'publication'}) AS nodes,
collect({source: a.author_id, target: p.publication_id, label: 'AUTHORS'}) AS edges
```

6. 删除新插入的节点和关系
```
MATCH (a:Author)-[r:AUTHORS]->(p:Paper)
WHERE a.author_id STARTS WITH 'test_' AND p.publication_id STARTS WITH 'test_'
DELETE r, a, p
```
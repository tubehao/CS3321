from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF
from collections import defaultdict
import csv

# 定义命名空间
COAUTHOR = Namespace("https://example.org/coauthor/")

# 创建一个新图来存储coauthor关系
coauthor_graph = Graph()

def load_data():
    coauthor_data = defaultdict(lambda: {'count': 0, 'interests': []})
    with open('coauthor_data.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)  # 跳过标题行
        for row in reader:
            author1, author2, count, interests1, interests2 = row
            coauthor_data[(URIRef(author1), URIRef(author2))]['count'] = int(count)
            coauthor_data[(URIRef(author1), URIRef(author2))]['interests'] = [interests1, interests2]
    return coauthor_data

coauthor_data = load_data()

# 将coauthor关系和合作次数存储到图中
for (author1, author2), data in coauthor_data.items():
    relation_node = URIRef(f"{author1}_coauthoredWith_{author2}_relation")
    coauthor_graph.add((relation_node, RDF.type, COAUTHOR.coauthor_relation))
    coauthor_graph.add((relation_node, COAUTHOR.coauthoredTimes, Literal(data['count'])))
    coauthor_graph.add((author1, COAUTHOR.hasCoauthorRelation, relation_node))
    coauthor_graph.add((author2, COAUTHOR.hasCoauthorRelation, relation_node))
    coauthor_graph.add((author1, COAUTHOR.researchInterests, Literal(data['interests'][0])))
    coauthor_graph.add((author2, COAUTHOR.researchInterests, Literal(data['interests'][1])))

# 将coauthor关系输出为TTL格式
output_file = "coauthor_output_lowmemory.ttl"
coauthor_graph.serialize(destination=output_file, format="ttl")

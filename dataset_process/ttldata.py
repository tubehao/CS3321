import nltk
import csv
from nltk.corpus import stopwords
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF
from collections import defaultdict
from sklearn.feature_extraction.text import CountVectorizer
import string
import gc

# 下载nltk数据包（仅需运行一次）
nltk.download('stopwords')

# 定义命名空间
DBLP = Namespace("https://dblp.org/rdf/schema#")

# 读取TTL文件
g = Graph()
g.parse("dblp.ttl", format="ttl")

# 初始化作者研究兴趣的字典
author_interests = defaultdict(list)

# 初始化用于存储作者姓名和URL的字典
author_details = defaultdict(dict)

# 获取英文停用词
stop_words = set(stopwords.words('english'))

# 全局实例化 CountVectorizer
vectorizer = CountVectorizer(max_features=10, stop_words='english')

def preprocess_text(text):
    # 移除标点并转换为小写
    return text.translate(str.maketrans('', '', string.punctuation)).lower()

def save_nodes_and_relationships(coauthor_count, author_interests, author_details):
    # 保存作者节点信息
    with open('nodes.csv', 'w', newline='') as node_file:
        node_writer = csv.writer(node_file)
        node_writer.writerow([":ID", "name", "url", "interests"])  # Neo4j要求的节点头格式

        # 写入Authors
        for author_url, details in author_details.items():
            name = details['name']
            interests = ", ".join(set(author_interests[author_url][:10]))  # 保留前10个兴趣
            node_writer.writerow([author_url, name, author_url, interests])  # 使用URL作为ID
    
    # 保存合作关系信息
    with open('relationships.csv', 'w', newline='') as rel_file:
        rel_writer = csv.writer(rel_file)
        rel_writer.writerow([":START_ID", ":END_ID", ":TYPE", "count"])  # Neo4j要求的关系头格式

        # 写入合作关系及合作次数
        for (author1, author2), count in coauthor_count.items():
            rel_writer.writerow([author1, author2, "COAUTHORED_WITH", count])

# 提取每个作者的关键词、姓名、URL并统计合作次数
coauthor_count = defaultdict(int)
for publication in g.subjects(RDF.type, DBLP.Publication):
    authors = list(g.objects(publication, DBLP.hasSignature))  # 使用hasSignature

    # 提取标题并生成兴趣关键词
    title = g.value(publication, DBLP.title)
    if title:
        title = preprocess_text(title)
        title_words = [title]
        try:
            vectorizer.fit_transform(title_words)
            keywords = vectorizer.get_feature_names_out()
        except ValueError:
            keywords = []

    # 从hasSignature中提取作者信息
    for signature in authors:
        author_url = g.value(signature, DBLP.signatureCreator)
        author_name = g.value(signature, DBLP.signatureDblpName)

        if author_url and author_name:
            author_url = str(author_url)
            author_details[author_url] = {'name': str(author_name), 'url': author_url}
            author_interests[author_url].extend(keywords)  # 继续处理研究兴趣
    
    # 计算作者之间的合作次数
    for i in range(len(authors)):
        for j in range(i + 1, len(authors)):
            author1 = str(g.value(authors[i], DBLP.signatureCreator))
            author2 = str(g.value(authors[j], DBLP.signatureCreator))
            if author1 and author2:
                coauthor_count[(author1, author2)] += 1

# 保存节点和关系数据到CSV文件
save_nodes_and_relationships(coauthor_count, author_interests, author_details)

# 清理内存
del coauthor_count
del g
gc.collect()  # 强制进行垃圾回收

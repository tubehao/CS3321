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

def save_data(coauthor_count, author_interests, author_details):
    with open('coauthor_data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Author1_Name', 'Author1_URL', 'Author2_Name', 'Author2_URL', 'Count', 'Interests1', 'Interests2'])
        for (author1, author2), count in coauthor_count.items():
            name1 = author_details[author1]['name']
            url1 = author_details[author1]['url']
            name2 = author_details[author2]['name']
            url2 = author_details[author2]['url']
            interests1 = ", ".join(set(author_interests[author1][:10]))  # 保留前10个兴趣
            interests2 = ", ".join(set(author_interests[author2][:10]))  # 保留前10个兴趣
            writer.writerow([name1, url1, name2, url2, count, interests1, interests2])

# 提取每个作者的关键词、姓名、URL并统计合作次数
coauthor_count = defaultdict(int)
for publication in g.subjects(RDF.type, DBLP.Publication):
    authors = list(g.objects(publication, DBLP.authoredBy))
    title = g.value(publication, DBLP.title)
    
    if title:
        title = preprocess_text(title)
        title_words = [title]
        try:
            vectorizer.fit_transform(title_words)
            keywords = vectorizer.get_feature_names_out()
        except ValueError:
            keywords = []

    for author in authors:
        # 获取每个作者的详细信息（姓名和URL）
        author_url = str(author)
        signature_node = g.value(author, DBLP.hasSignature)
        if signature_node:
            author_name = g.value(signature_node, DBLP.signatureDblpName)
            if author_name:
                author_details[author_url] = {'name': str(author_name), 'url': author_url}
        
        # 如果已经获取到名字和URL，继续处理研究兴趣
        author_interests[author_url].extend(keywords)
    
    # 计算作者之间的合作次数
    for i in range(len(authors)):
        for j in range(i + 1, len(authors)):
            author1 = str(authors[i])
            author2 = str(authors[j])
            coauthor_count[(author1, author2)] += 1

# 保存合作次数和研究兴趣到CSV文件
save_data(coauthor_count, author_interests, author_details)

del coauthor_count
del g  # 如果不再需要原始图
gc.collect()  # 强制进行垃圾回收

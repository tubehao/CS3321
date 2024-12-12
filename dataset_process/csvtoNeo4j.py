from neo4j import GraphDatabase
from tqdm import tqdm
import csv

uri = "bolt://localhost:7687"  # 修改为您的bolt端口
user = "neo4j"  # 默认用户，根据实际情况修改
password = "password"  # 修改为您的密码

class CoauthorGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def import_coauthors(self, file_path):
        with self.driver.session() as session:
            # 打开CSV文件并读取
            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                next(reader)  # 跳过标题行
                # 使用tqdm展示进度条
                for row in tqdm(reader, desc="Importing coauthor data"):
                    author1_name, author1_url, author2_name, author2_url, count, interests1, interests2 = row
                    session.write_transaction(
                        self.create_coauthor_relation, 
                        author1_name, author1_url, author2_name, author2_url, 
                        int(count), interests1, interests2
                    )

    @staticmethod
    def create_coauthor_relation(tx, author1_name, author1_url, author2_name, author2_url, count, interests1, interests2):
        # Neo4j查询语句，创建节点和关系
        query = (
            "MERGE (a1:Author {name: $author1_name, url: $author1_url}) "
            "MERGE (a2:Author {name: $author2_name, url: $author2_url}) "
            "MERGE (a1)-[r:COAUTHORED_WITH {count: $count}]->(a2) "
            "SET a1.interests = $interests1, a2.interests = $interests2 "
            "RETURN r"
        )
        # 执行查询
        result = tx.run(query, 
                        author1_name=author1_name, 
                        author1_url=author1_url, 
                        author2_name=author2_name, 
                        author2_url=author2_url, 
                        count=count, 
                        interests1=interests1, 
                        interests2=interests2)
        return result.single()[0]

if __name__ == "__main__":
    # 实例化并开始导入
    coauthor_graph = CoauthorGraph(uri, user, password)
    coauthor_graph.import_coauthors('coauthor_data.csv')  # CSV文件路径
    coauthor_graph.close()

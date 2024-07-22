# chat/routes.py

from flask import Blueprint, request, jsonify, current_app, render_template
from neo4j import GraphDatabase
import re

blueprint = Blueprint('chat', __name__, url_prefix='/chat')

@blueprint.route('/chat.html')
def index():
    databases = current_app.config['DATABASES']
    return render_template('/home/chat.html', databases=databases)

@blueprint.route('/set_database', methods=['POST'])
def set_database():
    data = request.get_json()
    selected_database = data['database']
    current_app.config['CURRENT_DATABASE'] = selected_database
    return jsonify({'status': 'success', 'selected_database': selected_database})

@blueprint.route('/get_response', methods=['POST'])
def get_response():
    data = request.get_json()
    user_message = data['message']
    
    # 使用初始化后的模型
    pipeline_prompt = current_app.config['MODEL_PIPELINE']
    pipeline_chat = current_app.config['MODEL_SOLUTION']
    pipeline_pure = current_app.config['MODEL_PURE']
    
    current_database = current_app.config.get('CURRENT_DATABASE', 'yago')
    query_prompt = current_app.config['QUERY_PROMPT'][current_database]
    
    # 构建提示以生成Cypher查询语句
    prompt = f"Our dataset contains a {query_prompt['type']} stored in a Neo4j database. With node including {query_prompt['label']} and uri. Translate the following natural language query into a Cypher query for Neo4j and wrap the query with '```' \n \n for example,{query_prompt['example']}.\nNatural Language Query: {user_message}\n\n\n\nCypher Query:"
    print(prompt)
    # 调用模型生成输出
    output = pipeline_prompt(prompt, max_new_tokens=100)
    generated_text = output[0]['generated_text'].strip()
    
    # 使用正则表达式提取用```包裹的Cypher查询
    match = re.search(r'```(.*?)```', generated_text[len(prompt):], re.DOTALL)
    if match:
        cypher_query = match.group(1).strip()
        print("~~~~~~~~~~~~~~~~~~~~~")
        print(cypher_query)
    else:
        cypher_query = "MATCH (n) RETURN n LIMIT 1"  # 默认查询语句，如果没有匹配到

    # 使用生成的Cypher查询语句在Neo4j中查询
    driver = current_app.config['NEO4J_DRIVER']
    with driver.session() as session:
        result = session.run(cypher_query)
        query_results = [record.data() for record in result]
    print(query_results)
    # 将查询结果转换为G6所需的数据格式
    graph_data = parse_neo4j_results(query_results)

    # 构建提示以让LLM解决问题
    result_prompt = f"Knowledge: {graph_data}. Use the knowledge to address the following question. Don't contain it in your answer directly, you can just refer to it. \n\n Question: {user_message}. \n Answer:"

    final_output = pipeline_chat(result_prompt, max_new_tokens=200)
    solution = final_output[0]['generated_text'].strip()

    pure_prompt = f"Address the following question. \n\n Question:{user_message}.Answer:"
    pure_output = pipeline_pure(pure_prompt, max_new_tokens=200)
    pure_solution = pure_output[0]['generated_text'].strip()
    
    # 返回解决方案
    return jsonify({
        "solution_part1": solution[len(result_prompt):],  # 第一部分
        "solution_part2": pure_solution[len(pure_prompt):],  # 第二部分
        "graph_data": graph_data  # 返回图表数据
    })

def parse_neo4j_results(results):
    graph_data = {"nodes": [], "edges": []}
    node_ids = set()

    for record in results:
        node = record['n']
        relationship = record.get('r')
        neighbor = record.get('neighbor')

        # 添加节点
        if node['uri'] not in node_ids:
            graph_data['nodes'].append({
                "id": node.get('uri'),
                "label": node.get('rdfs__label', 'Unknown'),
                "comment": node.get('rdfs__comment', ''),
                "image": node.get('sch__image', '')
            })
            node_ids.add(node.get('uri'))

        if neighbor['uri'] and neighbor['uri'] not in node_ids:
            graph_data['nodes'].append({
                "id": neighbor['uri'],
                "label": neighbor.get('rdfs__label', 'Unknown'),
                "comment": neighbor.get('rdfs__comment', ''),
                "image": neighbor.get('sch__image', '')
            })
            node_ids.add(neighbor['uri'])

        # 添加边
        graph_data['edges'].append({
            "source": node['uri'],
            "target": neighbor['uri'],
            "type": relationship[1]
        })

    return graph_data

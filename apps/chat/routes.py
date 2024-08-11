from flask import Blueprint, request, jsonify, current_app, render_template
from neo4j import GraphDatabase
import re
import json
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
    # output = pipeline_prompt(prompt, max_new_tokens=100)
    # generated_text = output[0]['generated_text'].strip()
    generated_text = get_model_response(pipeline_prompt, prompt)
    
    # 使用正则表达式提取用```包裹的Cypher查询
    match = re.search(r'```(.*?)```', generated_text, re.DOTALL)
    cypher_query = None
    if match:
        cypher_query = match.group(1).strip()
        print("~~~~~~~~~~~~~~~~~~~~~")
        print(cypher_query)
        driver = current_app.config['NEO4J_DRIVER']
        try:
            with driver.session() as session:
                result = session.run(cypher_query, timeout=10)  # 设置超时时间为10秒
                query_results = [record.data() for record in result]
        except:
            # logging.error(f"Query timed out or service unavailable: {e}")
            query_results = []
    else:
        # cypher_query = "MATCH (n) RETURN n LIMIT 1"  # 默认查询语句，如果没有匹配到
        query_results = []
    # cypher_query = "MATCH (n)-[r]-(neighbor) WHERE n.rdfs__label CONTAINS 'Basketball' RETURN n, r, neighbor LIMIT 25"

    # 使用生成的Cypher查询语句在Neo4j中查询
    
    # print(query_results)
    # 将查询结果转换为G6所需的数据格式
    graph_data = parse_neo4j_results(query_results)
    print(graph_data)

    # 构建提示以让LLM解决问题
    knowledge = str(graph_data)
    result_prompt = f"Knowledge: {knowledge[0:4000]}. Use the knowledge to address the following question. Don't contain it in your answer directly, you can just refer to it. \n\n Question: {user_message}. \n Answer:"

    # final_output = pipeline_chat(result_prompt, max_new_tokens=200)
    # solution = final_output[0]['generated_text'].strip()
    solution = get_model_response(pipeline_chat, result_prompt)

    pure_prompt = f"Address the following question. \n\n Question:{user_message}.Answer:"
    # pure_output = pipeline_pure(pure_prompt, max_new_tokens=200)
    # pure_solution = pure_output[0]['generated_text'].strip()
    pure_solution = get_model_response(pipeline_pure, pure_prompt)
    visualize_data = get_model_response(pipeline_pure, f"""Change the answer to the format that I can visualize by G6 such as {{
                            "nodes": [{{ "id": "node1" }}, {{ "id": "node2" }}],
                            "edges": [{{ "source": "node1", "target": "node2" }}]
                            }}. your response should be able to convert by eval function in python. Answer: {solution}""")
    explanation = get_model_response(pipeline_pure, f"Explain the answer and the graph. Answer:{solution}, graph:{graph_data}")
    print(visualize_data)
    try:
        visualize_data_dict = eval(visualize_data)
        if isinstance(visualize_data_dict, dict) and all(isinstance(v, list) and all(isinstance(i, dict) for i in v) for v in visualize_data_dict.values()):
            visualize_data = visualize_data_dict
        else:
            raise ValueError("Generated data is not in the expected format.")
    except Exception as e:
        print(f"Error parsing visualize_data: {e}")
        visualize_data = {}
    # 返回解决方案

    # print(type(visualize_data["nodes"]))
    print(cypher_query)
    return jsonify({
        "solution_part1": solution,  # 第一部分
        "solution_part2": pure_solution,  # 第二部分
        "graph_data": graph_data,  # 返回图表数据
        "visualize_data": visualize_data,  # 返回可视化数据
        "query" : cypher_query,
        "explanation": explanation
    })

def get_model_response(pipeline, prompt):
    if "llama" in current_app.config["MODEL_ID"]:
        output = pipeline(prompt, max_new_tokens=200)
        generated_text = output[0]['generated_text'].strip()
        return generated_text[len(prompt):]
    elif "gpt" in current_app.config["MODEL_ID"]:
        return pipeline(prompt, max_tokens=2000)


def parse_neo4j_results(results):
    graph_data = {"nodes": [], "edges": []}
    node_ids = set()

    for record in results:
        node = record['n']
        node_uri = node.get('uri', '')
        node_label = node.get('ns0__label', node_uri)
        node_comment = node.get('rdfs__comment', '')
        node_year_of_publication = node.get('ns2__yearOfPublication', None)
        node_published_in = node.get('ns2__publishedIn', None)
        node_title = node.get('ns2__title', None)
        
        # 添加节点
        # if node_uri not in node_ids:
        node_data = {
            "id": node_label,
            # "uri": node_uri,
            # "label": node_label,
            # "data": node_label,
            "comment": node_comment,
            # "year_of_publication": node_year_of_publication,
            # "published_in": node_published_in,
            # "title": node_title,
        }
        graph_data['nodes'].append(node_data)
        # node_ids.add(node_uri)

        # 处理关系和邻居节点（如果存在）
        relationship = record.get('r')
        neighbor = record.get('neighbor')

        if relationship and neighbor:
            neighbor_uri = neighbor.get('uri', '')
            neighbor_label = neighbor.get('ns0__label', neighbor_uri)
            neighbor_comment = neighbor.get('rdfs__comment', '')
            # neighbor_image = neighbor.get('sch__image', neighbor.get('ns2__image', ''))

            # 添加邻居节点
            neighbor_data = {
                "id": neighbor_label,
                # "label": neighbor_label,
                "comment": neighbor_comment,
                # "image": neighbor_image
            }
            graph_data['nodes'].append(neighbor_data)

            # 添加边
            graph_data['edges'].append({
                "source": node_label, 
                "target": neighbor_label,
                # "type": relationship[1]  # 假设relationship是一个三元组 (start_node, relationship_type, end_node)
            })

    return graph_data

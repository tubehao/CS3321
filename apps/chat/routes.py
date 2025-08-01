from flask import Blueprint, render_template, request, jsonify, current_app, session
from neo4j import GraphDatabase
from flask_login import login_required, current_user
import re
import json
blueprint = Blueprint('chat', __name__, url_prefix='/chat')

@blueprint.route('/chat.html')
@login_required
def index():
    databases = current_app.config['DATABASES']
    return render_template('/home/chat.html', databases=databases)

@blueprint.route('/chat_history', methods=['GET'])
@login_required
def chat_history():
    chat_history = session.get(f'{current_user.id}_chat_history', [])
    # print(chat_history)
    return jsonify(chat_history)

@blueprint.route('/like_message', methods=['POST'])
def like_message():
    data = request.get_json()
    message_id = data.get('message_id')
    sender = data.get('sender')

    # 假设我们将点赞存储在数据库或文件中
    # print(f"Message ID: {message_id}, Sender: {sender} liked")

    # 这里您可以执行实际的点赞操作，例如更新数据库
    # 返回成功响应
    return jsonify({"status": "success", "message": "Liked successfully"})

@blueprint.route('/chat/record_answer_choice', methods=['POST'])
def record_answer_choice():
    data = request.get_json()
    message_id = data['message_id']
    selected_answer = data['selected_answer']
    
    # 在此处记录用户选择，可以保存到数据库或日志文件
    # print(f"Message ID: {message_id}, User selected: {selected_answer}")
    
    # 返回成功的响应
    return jsonify({'status': 'success', 'message': 'Answer choice recorded'})

@blueprint.route('/set_database', methods=['POST'])
@login_required
def set_database():
    data = request.get_json()
    selected_database = data['database']
    current_app.config['CURRENT_DATABASE'] = selected_database
    uri = current_app.config["DATABASES_URI"][current_app.config.get('CURRENT_DATABASE', 'default')]
    current_app.config['NEO4J_DRIVER'] = GraphDatabase.driver(uri)
    return jsonify({'status': 'success', 'selected_database': selected_database})

@blueprint.route('/get_response', methods=['POST'])
@login_required
def get_response():
    data = request.get_json()
    user_message = data['message']
    
    # 使用初始化后的模型
    pipeline_prompt = current_app.config['MODEL_PIPELINE']
    pipeline_chat = current_app.config['MODEL_SOLUTION']
    pipeline_pure = current_app.config['MODEL_PURE']
    pipeline_visual = current_app.config['MODEL_VISUAL']
    
    current_database = current_app.config.get('CURRENT_DATABASE', 'dblp')
    query_prompt = current_app.config['QUERY_PROMPT'][current_database]
    
    # 构建提示以生成Cypher查询语句
    prompt = f"""Our dataset contains a {query_prompt['type']} stored in a Neo4j database. With node including {query_prompt['label']} and uri. 
    Translate the following natural language query into a Cypher query for Neo4j and wrap the query with '```'. 
    The format of query result should be able to visualize by G6 such as {{"nodes": [], "edges": []}} while all the label and id should be string.
    for example, {query_prompt['example']}. The relation is always named 'AUTHORS' and you should not change it.
    You should always set the limit of the return.
    Natural Language Query: {user_message}\n\n\n\nCypher Query:"""
    
    generated_text = get_model_response(pipeline_prompt, prompt)
    
    # 使用正则表达式提取用```包裹的Cypher查询
    match = re.search(r'```(.*?)```', generated_text, re.DOTALL)
    cypher_query = None
    if match:
        cypher_query = match.group(1).strip()
        print("###### Generated Cypher Query ######")
        print(cypher_query)
        driver = current_app.config['NEO4J_DRIVER']
        try:
            with driver.session() as neo4jsession:
                result = neo4jsession.run(cypher_query, timeout=10)  # 设置超时时间为10秒
                query_results = result.data()

        except:
            query_results = None
    else:
        query_results = None
    # print("###### Query results ######")
    # print(query_results)
    graph_data = query_results[0] if query_results else {}
    print("###### Graph Data ######")
    print(graph_data)

    knowledge = str(graph_data)
    result_prompt = f"Knowledge: {knowledge[0:3000]}. Use the knowledge to address the following question. Don't contain it in your answer directly, you can just refer to it. \n\n Question: {user_message}. \n Answer:"

    solution = get_model_response(pipeline_chat, result_prompt)

    visualize_solution = solution[:2000] if len(solution) > 2000 else solution
    visualize_data = get_model_response(pipeline_chat, f"""Change the answer to the format that can be visualized by G6: {{
                            "nodes": [{{ "id": "node1" }}, {{ "id": "node2" }}],
                            "edges": [{{ "source": "node1", "target": "node2" }}]
                            }}. your response should be able to convert by eval function in python, answer the data only, don't contain any other symbol. Answer: {visualize_solution}, Graph Data:{str(graph_data)[:2000]}""")
    explanation = get_model_response(pipeline_chat, f"Explain the answer and the graph. Answer:{visualize_solution}, Graph Data:{str(visualize_data)[:2000]}")
    
    print("###### Visualize Data ######")
    print(visualize_data)
    try:
        if visualize_data.startswith("```json") and visualize_data.endswith("```"):
            visualize_data = visualize_data[7:-3].strip()
        visualize_data_dict = eval(visualize_data)
        # visualize_data_dict = json.loads(visualize_data)
        if isinstance(visualize_data_dict, dict) and all(isinstance(v, list) and all(isinstance(i, dict) for i in v) for v in visualize_data_dict.values()):
            visualize_data = visualize_data_dict
        else:
            raise ValueError("Generated data is not in the expected format.")
    except Exception as e:
        print(f"Error parsing visualize_data: {e}")
        visualize_data = {"nodes": [], "edges": []}
    # 保存用户消息和系统响应到会话中
    chat_history = session.get(f'{current_user.id}_chat_history', [])
    chat_history.append({'sender': 'user', 'message': user_message})
    chat_history.append({'sender': 'bot', 'message': {
        "solution_part1": solution,
        "graph_data": graph_data,
        "visualize_data": visualize_data,
        "query": cypher_query,
        "explanation": explanation
    }})

    # 将更新后的历史记录存回 session
    session[f'{current_user.id}_chat_history'] = chat_history

    return jsonify({
        "solution_part1": solution,
        "graph_data": graph_data,
        "visualize_data": visualize_data,
        "query" : cypher_query,
        "explanation": explanation
    })


@blueprint.route('/clear_history', methods=['POST'])
@login_required
def clear_history():
    session.pop(f'{current_user.id}_chat_history', None)
    return jsonify({'status': 'Chat history cleared'})


def get_model_response(pipeline, prompt):
    if "gpt" in current_app.config["MODEL_ID"]:
        response = pipeline(prompt)
        if not isinstance(response, str):
            return response.content
        else:
            return response
    elif "qwen" in current_app.config["MODEL_ID"]:
        # TODO
        response = pipeline.chat.completions.create(
            model="qwen-max", # https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=[
                # {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt}
            ]
        )
        return response.choices[0].message.content
    else:
        raise ValueError("Unsupported model type")
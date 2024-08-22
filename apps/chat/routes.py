from flask import Blueprint, render_template, request, jsonify, current_app, session
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
    return jsonify(chat_history)

@blueprint.route('/set_database', methods=['POST'])
@login_required
def set_database():
    data = request.get_json()
    selected_database = data['database']
    current_app.config['CURRENT_DATABASE'] = selected_database
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
    
    current_database = current_app.config.get('CURRENT_DATABASE', 'yago')
    query_prompt = current_app.config['QUERY_PROMPT'][current_database]
    
    # 构建提示以生成Cypher查询语句
    prompt = f"""Our dataset contains a {query_prompt['type']} stored in a Neo4j database. With node including {query_prompt['label']} and uri. 
    Translate the following natural language query into a Cypher query for Neo4j and wrap the query with '```'. The format of query result should be able to visualize by G6 such as {{"nodes": [], "edges": []}} while all the label and id should be string.
    for example,{query_prompt['example']}.
    Natural Language Query: {user_message}\n\n\n\nCypher Query:"""
    
    generated_text = get_model_response(pipeline_prompt, prompt)
    
    # 使用正则表达式提取用```包裹的Cypher查询
    match = re.search(r'```(.*?)```', generated_text, re.DOTALL)
    cypher_query = None
    if match:
        cypher_query = match.group(1).strip()
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
    print(query_results)
    graph_data = query_results[0] if query_results else {}

    knowledge = str(graph_data)
    result_prompt = f"Knowledge: {knowledge[0:3000]}. Use the knowledge to address the following question. Don't contain it in your answer directly, you can just refer to it. \n\n Question: {user_message}. \n Answer:"

    solution = get_model_response(pipeline_chat, result_prompt)

    pure_prompt = f"Address the following question. \n\n Question:{user_message}.Answer:"
    pure_solution = get_model_response(pipeline_pure, pure_prompt)

    visualize_solution = solution[:2000] if len(solution) > 2000 else solution
    visualize_data = get_model_response(pipeline_chat, f"""Change the answer to the format that can be visualized by G6 such as {{
                            "nodes": [{{ "id": "node1" }}, {{ "id": "node2" }}],
                            "edges": [{{ "source": "node1", "target": "node2" }}]
                            }}. your response should be able to convert by eval function in python, answer the data only, don't contain any other symbol. Answer: {visualize_solution}, Graph Data:{str(graph_data)[:2000]}""")
    explanation = get_model_response(pipeline_chat, f"Explain the answer and the graph. Answer:{visualize_solution}, Graph Data:{str(visualize_data)[:2000]}")
    
    try:
        visualize_data_dict = eval(visualize_data)
        if isinstance(visualize_data_dict, dict) and all(isinstance(v, list) and all(isinstance(i, dict) for i in v) for v in visualize_data_dict.values()):
            visualize_data = visualize_data_dict
        else:
            raise ValueError("Generated data is not in the expected format.")
    except Exception as e:
        print(f"Error parsing visualize_data: {e}")
        visualize_data = {"nodes": [], "edges": []}
    print(graph_data)
    # 保存用户消息和系统响应到会话中
    chat_history = session.get(f'{current_user.id}_chat_history', [])
    chat_history.append({'sender': 'user', 'message': user_message})
    chat_history.append({'sender': 'bot', 'message': {
        "solution_part1": solution,
        "solution_part2": pure_solution,
        "graph_data": graph_data,
        "visualize_data": visualize_data,
        "query": cypher_query,
        "explanation": explanation
    }})

    # 将更新后的历史记录存回 session
    session[f'{current_user.id}_chat_history'] = chat_history

    return jsonify({
        "solution_part1": solution,
        "solution_part2": pure_solution,
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
    if "llama" in current_app.config["MODEL_ID"]:
        output = pipeline(prompt, max_new_tokens=200)
        generated_text = output[0]['generated_text'].strip()
        return generated_text[len(prompt):]
    elif "gpt" in current_app.config["MODEL_ID"]:
        response = pipeline(prompt)
        if not isinstance(response, str):
            return response.content
        else:
            return response
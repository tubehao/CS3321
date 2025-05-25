# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from jinja2 import TemplateNotFound


from flask import Blueprint, render_template, request, jsonify, current_app, session
from neo4j import GraphDatabase
from flask_login import login_required, current_user
import re
import json

blueprint = Blueprint('home', __name__) # Already registered in apps/__init__.py

@blueprint.route('/index')
@login_required
def index():
    return render_template('home/index.html', segment='index')

@blueprint.route('/query_history', methods=['GET'])
@login_required
def query_history():
    query_history = session.get(f'{current_user.id}_query_history', [])
    return jsonify(query_history)

@blueprint.route('/clear_query', methods=['POST'])
@login_required
def clear_query():
    session.pop(f'{current_user.id}_query_history', None)
    return jsonify({'status': 'Query history cleared'})

@blueprint.route('/send_query', methods=['POST'])
@login_required
def send_query():
    data = request.get_json()
    user_message = data['message']

    current_database = current_app.config.get('CURRENT_DATABASE', 'dblp')
    driver = current_app.config['NEO4J_DRIVER']

    try:
        with driver.session() as neo4jsession:
            result = neo4jsession.run(user_message, timeout=10)
            query_results = result.data()
    except:
        query_results = None
    
    query_history = session.get(f'{current_user.id}_query_history', [])
    # query_history.append({'sender': 'user', 'message': user_message})
    query_history.append({'sender': 'database', 'message': {
        'query_results': query_results,
    }})
    session[f'{current_user.id}_query_history'] = query_history

    # print(query_results[0])
    # print(query_results)
    if isinstance(query_results, list) and len(query_results) > 0:
        return jsonify({
            "query_results": query_results[0],
        })
    else:
        return jsonify({
            "query_results": None,
        })



@blueprint.route('/<template>')
# @login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        print("home/" + template, segment)
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None

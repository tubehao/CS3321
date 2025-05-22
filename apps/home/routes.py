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


@blueprint.route('/send_query', methods=['POST'])
@login_required
def send_query():
    print("send_query")
    return jsonify({'status': 'Send Query'})



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

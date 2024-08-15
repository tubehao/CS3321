from flask import Blueprint, request, jsonify, current_app, render_template
from neo4j import GraphDatabase
import re
import os
from werkzeug.utils import secure_filename
import csv
import subprocess

blueprint = Blueprint('table', __name__, url_prefix='/table')

@blueprint.route('/')
def index():
    return render_template('table.html')

@blueprint.route('/upload', methods=['POST'])
def upload_file():
    # return jsonify(success=True)
    if 'file' not in request.files:
        return jsonify(success=False, message="No file part")
    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, message="No selected file")
    if file and allowed_file(file.filename):
        print(file.filename)
        filename = secure_filename(file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # 检查并创建上传目录
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        file_path = os.path.join(upload_folder, filename)
        print(file_path)
        file.save(file_path)
        print("saved")
        try:
            rdf_file_path = copy_file_to_docker(file_path)
            import_to_neo4j(rdf_file_path)
            return jsonify(success=True)
        except Exception as e:
            return jsonify(success=False, message=str(e))
    return jsonify(success=False, message="File not allowed")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'ttl'}


def import_to_neo4j(file_path):
    driver = current_app.config['NEO4J_DRIVER']

    import_query = """
    CALL n10s.rdf.import.fetch("file://{rdf_file_path}", "Turtle")
    """.format(rdf_file_path=file_path)
    
    with driver.session() as session:
        result = session.run(import_query)
        for record in result:
            print(record)

def copy_file_to_docker(file_path, docker_container_name = 'yago', target_path = '/var/lib/neo4j/import'):
    docker_cp_command = ["docker", "cp", file_path, f"{docker_container_name}:{target_path}"]
    try:
        subprocess.run(docker_cp_command, check=True)
        print("File copied to Docker container successfully.")
        return target_path
    except subprocess.CalledProcessError as e:
        print(f"Failed to copy file to Docker container: {e}")

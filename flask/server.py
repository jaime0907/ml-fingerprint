from flask import Flask, request, render_template, send_from_directory
import sqlite3
import os
import json
from datetime import datetime
#from flask_kerberos import requires_authentication, init_kerberos


database = os.path.join(os.getcwd(), 'ml_fingerprint_database.db')

def get_db_connection():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__, static_folder='assets')

@app.route('/', methods=['GET'])
#@requires_authentication
def main_page():
    return render_template('index.html')

@app.route('/model/<modelname>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_model(modelname):
    if request.method == 'GET':
        return get_model(modelname)
    elif request.method == 'POST':
        return upload_model(modelname)
    elif request.method == 'PUT':
        return update_model(modelname)
    elif request.method == 'DELETE':
        return delete_model(modelname)
    else:
        return "Method not allowed.", 405

def get_model(modelname):
    conn = get_db_connection()
    c = conn.cursor()

    model = None
    if 'version' in request.args:
        version = request.args['version']
        model = c.execute('select * from models where name = ? and version = ?', (modelname,version)).fetchone()
    else:
        model = c.execute('select * from models where name = ? order by version desc', (modelname,)).fetchone()
    
    if model != None:
        model_dict = dict(model)
        model_dict['scores'] = json.loads(model['scores'])
        model_dict['metadata'] = json.loads(model['metadata'])

        json_response = json.dumps(model_dict, indent=4)
        return (json_response, {'Content-Type': 'application/json'})
    else:
        return ("The selected model doesn't exist.", 400)

def upload_model(modelname):
    conn = get_db_connection()
    c = conn.cursor()

    body = request.json
    print(body)
    model = c.execute('select * from models where name = ? and version = ?', (modelname,body['version'])).fetchone()

    if model == None:
        model_dict = dict(body)
        model_dict['supervised'] = 0
        if body['supervised'] == "true":
            model_dict['supervised'] = 1

        model_dict['scores'] = json.dumps(body['scores'])
        model_dict['metadata'] = json.dumps(body['metadata'])
        model_dict['name'] = modelname
        
        c.execute('insert into models (name, serialized_model, serializer_bytes, serializer_text, supervised, type, estimator, scores, version, metadata, date, description, owner) values (:name, :serialized_model, :serializer_bytes, :serializer_text, :supervised, :type, :estimator, :scores, :version, :metadata, :date, :description, :owner)',
            model_dict)

        conn.commit()
        return "The model has been successfully inserted into the database.", 200
    else:
        return "The model already exists.", 400

def update_model(modelname):
    conn = get_db_connection()
    c = conn.cursor()

    body = request.json

    model = c.execute('select * from models where name = ? and version = ?', (modelname,body['version'])).fetchone()
    if model != None:
        model_dict = dict(body)
        model_dict['supervised'] = 0
        if body['supervised'] == "true":
            model_dict['supervised'] = 1

        model_dict['scores'] = json.dumps(body['scores'])
        model_dict['metadata'] = json.dumps(body['metadata'])
        model_dict['id'] = model['id']

        c.execute('update models set serialized_model = :serialized_model, serializer_bytes = :serializer_bytes, serializer_text = :serializer_text, supervised = :supervised, type = :type, estimator = :estimator, scores = :scores, metadata = :metadata, date = :date, description = :description, owner = :owner where id = :id',
            model_dict)

        conn.commit()
        return "The model has been successfully updated.", 200
    else:
        return "The model doesn't exist.", 404

def delete_model(modelname):
    conn = get_db_connection()
    c = conn.cursor()

    model = None
    if 'version' in request.args:
        version = request.args['version']
        model = c.execute('select * from models where name = ? and version = ? order by version desc', (modelname,version)).fetchone()
    else:
        model = c.execute('select * from models where name = ? order by version desc', (modelname,)).fetchone()

    if model != None:
        c.execute('delete from models where id = ?', (model['id'],))
        conn.commit()
        return "The model has been successfully deleted from the database.", 200
    else:
        return "The model doesn't exist.", 404




@app.route('/modellist', methods=['GET'])
def manage_modellist():
    if request.method == 'GET':
        return get_modellist()
    else:
        return "Method not allowed.", 405

@app.route('/modellist/<modelname>', methods=['GET'])
def manage_modellist_versions(modelname):
    if request.method == 'GET':
        return get_modellist(modelname)
    else:
        return "Method not allowed.", 405



def get_modellist(modelname=None):
    conn = get_db_connection()
    c = conn.cursor()

    sql_sentence = "select * from (select * from models order by version desc) where 1 = 1"
    args = {}
    
    # If type specified, filter by type
    if 'type' in request.args:
        model_type = request.args['type']
        if model_type == "supervised":
            sql_sentence += " and supervised = 1"
        elif model_type == "unsupervised":
            sql_sentence += " and supervised = 0"
        else:
            sql_sentence += " and type = :model_type"
            args['model_type'] = model_type

    # If modelname is specified, filter by that modelname and bypass 'allversions' filter
    if modelname != None:
        sql_sentence += " and name = :name"
        args['name'] = modelname

    # If allversions=true, show all versions. If not, show only lastest version for each model.
    if not ('allversions' in request.args and request.args['allversions'] == "true") and modelname == None:
        sql_sentence += " group by name"

    sql_sentence += " order by supervised desc, type, name"

    rows = c.execute(sql_sentence, args).fetchall()
    model_list = []
    for model in rows:
        model_dict = dict(model)
        model_dict['scores'] = json.loads(model['scores'])
        model_dict['metadata'] = json.loads(model['metadata'])
        
        model_list.append(model_dict)

    if 'format' in request.args and request.args['format'] == 'json':
        json_list = json.dumps(model_list, indent=4)
        return (json_list, {'Content-Type': 'application/json'})
    else:
        for model in model_list:
            new_scores = {}
            for key, value in model['scores'].items():
                new_scores[key] = "{:.4f}".format(value)
            model['scores'] = new_scores
            if model['date'] == None:
                date_str = "-"
            else:
                date = datetime.fromisoformat(str(model['date']))
                date_str = date.strftime('%d %b. %Y %H:%M')
            model['date'] = date_str
        return render_template('list.html', modelcount=len(model_list), modellist=model_list)

if __name__ == '__main__':
    #init_kerberos(app, hostname='EXAMPLE.COM')
    app.run(debug=True, host='0.0.0.0')
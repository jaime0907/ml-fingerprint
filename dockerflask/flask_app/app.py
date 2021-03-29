from flask import Flask, request, render_template, url_for, session, redirect
import sqlite3
import os
import json
from datetime import datetime, timedelta
from authlib.integrations.flask_client import OAuth
import secrets

database = os.path.join(os.getcwd(), 'ml_fingerprint_database.db')

def get_db_connection():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

server = Flask(__name__, static_folder='assets')
server.secret_key = '!secret'
server.config.from_object('config')
oauth = OAuth(server)

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)


@server.route('/', methods=['GET'])
def main_page():
    login = 'user' not in session
    user = ""
    if not login:
        user = session['user']
    return render_template('index.html', login=login, user=user)


@server.route('/login')
def login():
    #redirect_uri = url_for('auth', _external=True)
    redirect_uri = 'https://dslab01.etsit.urjc.es/mlfingerprint/auth'
    return oauth.google.authorize_redirect(redirect_uri)


@server.route('/auth')
def auth():
    token = oauth.google.authorize_access_token()
    user = oauth.google.parse_id_token(token)
    session['user'] = user
    return redirect('/mlfingerprint/')

@server.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/mlfingerprint/')
    

@server.route('/profile')
def profile():
    
    login = 'user' not in session
    user = ""
    if not login:
        user = session['user']

    conn = get_db_connection()
    c = conn.cursor()

    if not login:
        api_key = ""
        expire_date_html = ""
        
        if request.args.get('generatekey') == "true":
            api_key = secrets.token_urlsafe(16)
            create_date = datetime.now()
            expire_date = create_date + timedelta(days=1)
            expire_date_html = expire_date.strftime("%a. %e %B %Y %H:%M")
            c.execute('delete from api_keys where email = ?', (user['email'],))
            c.execute('insert into api_keys (email, key, create_date, expire_date, name) values (?,?,?,?,?)', (user['email'], api_key, create_date.isoformat(), expire_date.isoformat(), user['name']))
            conn.commit()
        else:
            row = c.execute('select * from api_keys where email = ? order by expire_date desc', (user['email'],)).fetchone()
            if row != None:
                api_key = row['key']
                expire_date = datetime.fromisoformat(row['expire_date'])
                expire_date_html = expire_date.strftime("%a. %e %B %Y %H:%M")

        return render_template('profile.html', login=login, user=user, api_key=api_key, expire_date=expire_date_html)
    else:
        return "403 Forbidden", 403


@server.route('/model/<modelname>', methods=['GET', 'POST', 'PUT', 'DELETE'])
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

    if 'api_key' not in request.args:
        return "No API key provided.", 403
    api_key = request.args['api_key']
    current_time = datetime.now()
    row = c.execute("select * from api_keys where key = ? and expire_date >= ?", (api_key, current_time.isoformat())).fetchone()
    if row == None:
        return "API key invalid", 403
    email = row['email']
    name = row['name']

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
        return ("The selected model doesn't exist.", 404)

def upload_model(modelname):
    conn = get_db_connection()
    c = conn.cursor()

    body = request.json
    print(body)

    if 'api_key' not in body:
        return "No API key provided.", 403
    api_key = body['api_key']
    current_time = datetime.now()
    row = c.execute("select * from api_keys where key = ? and expire_date >= ?", (api_key, current_time.isoformat())).fetchone()
    if row == None:
        return "API key invalid", 403
    email = row['email']
    name = row['name']

    model = c.execute('select * from models where name = ? and version = ?', (modelname,body['version'])).fetchone()

    if model == None:
        model_dict = dict(body)
        model_dict['supervised'] = 0
        if body['supervised'] == "true":
            model_dict['supervised'] = 1

        model_dict['scores'] = json.dumps(body['scores'])
        model_dict['metadata'] = json.dumps(body['metadata'])
        model_dict['name'] = modelname
        model_dict['owner'] = name
        model_dict['email'] = email

        c.execute('insert into models (name, serialized_model, serializer_bytes, serializer_text, supervised, type, estimator, scores, version, metadata, date, description, owner, email) values (:name, :serialized_model, :serializer_bytes, :serializer_text, :supervised, :type, :estimator, :scores, :version, :metadata, :date, :description, :owner, :email)',
            model_dict)

        conn.commit()
        return "The model has been successfully inserted into the database.", 200
    else:
        return "The model already exists.", 400

def update_model(modelname):
    conn = get_db_connection()
    c = conn.cursor()

    body = request.json

    if 'api_key' not in body:
        return "No API key provided.", 403
    api_key = body['api_key']
    current_time = datetime.now()
    row = c.execute("select * from api_keys where key = ? and expire_date >= ?", (api_key, current_time.isoformat())).fetchone()
    if row == None:
        return "API key invalid", 403
    email = row['email']
    name = row['name']

    model = c.execute('select * from models where name = ? and version = ?', (modelname,body['version'])).fetchone()
    if model != None:
        model_dict = dict(body)
        model_dict['supervised'] = 0
        if body['supervised'] == "true":
            model_dict['supervised'] = 1

        model_dict['scores'] = json.dumps(body['scores'])
        model_dict['metadata'] = json.dumps(body['metadata'])
        model_dict['id'] = model['id']
        model_dict['owner'] = name
        model_dict['email'] = email

        c.execute('update models set serialized_model = :serialized_model, serializer_bytes = :serializer_bytes, serializer_text = :serializer_text, supervised = :supervised, type = :type, estimator = :estimator, scores = :scores, metadata = :metadata, date = :date, description = :description, owner = :owner, email = :email where id = :id',
            model_dict)

        conn.commit()
        return "The model has been successfully updated.", 200
    else:
        return "The model doesn't exist.", 404

def delete_model(modelname):
    conn = get_db_connection()
    c = conn.cursor()

    if 'api_key' not in request.args:
        return "No API key provided.", 403
    api_key = request.args['api_key']
    current_time = datetime.now()
    row = c.execute("select * from api_keys where key = ? and expire_date >= ?", (api_key, current_time.isoformat())).fetchone()
    if row == None:
        return "API key invalid", 403
    email = row['email']
    name = row['name']

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




@server.route('/modellist', methods=['GET'])
def manage_modellist():
    if request.method == 'GET':
        return get_modellist()
    else:
        return "Method not allowed.", 405

@server.route('/modellist/<modelname>', methods=['GET'])
def manage_modellist_versions(modelname):
    if request.method == 'GET':
        return get_modellist(modelname)
    else:
        return "Method not allowed.", 405



def get_modellist(modelname=None):
    login = 'user' not in session
    user = ""
    if not login:
        user = session['user']

    conn = get_db_connection()
    c = conn.cursor()

    if 'format' in request.args and request.args['format'] == 'json':
        if 'api_key' not in request.args:
            return "No API key provided.", 403
        api_key = request.args['api_key']
        current_time = datetime.now()
        row = c.execute("select * from api_keys where key = ? and expire_date >= ?", (api_key, current_time.isoformat())).fetchone()
        if row == None:
            return "API key invalid", 403

    
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
        model_dict.pop('serialized_model')
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
        return render_template('list.html', modelcount=len(model_list), modellist=model_list, login=login, user=user)


#if __name__ == '__main__':
#    app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'), threaded=True)
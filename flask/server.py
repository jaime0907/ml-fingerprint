from flask import Flask, request
import sqlite3
import os

database = os.path.join(os.getcwd(), 'ml_fingerprint_database.db')

def get_db_connection():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)

@app.route('/getmodel')
def send_model():
    conn = get_db_connection()
    c = conn.cursor()
    modelname = request.args['modelname']
    print(modelname)
    model = c.execute('select * from models where name = ?', (modelname,)).fetchone()
    if model != None:
        return (model['model'], {'Content-Type': 'application/octet-stream'})
    else:
        return ("The selected model doesn't exist.", 404)
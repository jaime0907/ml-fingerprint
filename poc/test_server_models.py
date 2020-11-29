from ml_fingerprint import main
from Crypto.PublicKey import RSA
import sqlite3
import pickle
import requests as req
import json
import base64
import example_models

url = 'http://localhost:5000/'

def insert_model(model, name, supervised, model_type, coefficients, version, metadata):

    pickled_model = pickle.dumps(model)
    b64bytes_model = base64.b64encode(pickled_model)
    b64string_model = b64bytes_model.decode('ascii')

    serializer_bytes = "pickle"
    serializer_text = "base64"
    estimator = type(model).__name__
    
    supervised_int = 0
    if supervised:
        supervised_int = 1

    data = {'name': name,
            'serialized_model': b64string_model,
            'serializer_bytes': serializer_bytes,
            'serializer_text': serializer_text,
            'supervised': supervised_int,
            'type': model_type,
            'estimator': estimator,
            'coefficients': coefficients,
            'version': version,
            'metadata': metadata
            }
    res = req.post(url + 'model/' + name, json=data)

def get_model(modelname, public_key, version=None):
    version_text = ""
    if version != None:
        version_text = "?version=" + version
    res = req.get(url + '/model/' + modelname + version_text)
    if res.status_code != 200:
        print(res.text)
    else:
        data = res.json()
        pickled_model = base64.b64decode(data['serialized_model'])
        model = pickle.loads(pickled_model)
        if main.isInyected(model):
            signIsGood = model.verify(public_key)
            if signIsGood:
                return model
            else:
                raise Exception("Sign verification failed.")
        else:
            return model

def update_model(model, name, supervised, model_type, coefficients, version, metadata):

    pickled_model = pickle.dumps(model)
    b64bytes_model = base64.b64encode(pickled_model)
    b64string_model = b64bytes_model.decode('ascii')

    serializer_bytes = "pickle"
    serializer_text = "base64"
    estimator = type(model).__name__
    
    supervised_int = 0
    if supervised:
        supervised_int = 1

    data = {'name': name,
            'serialized_model': b64string_model,
            'serializer_bytes': serializer_bytes,
            'serializer_text': serializer_text,
            'supervised': supervised_int,
            'type': model_type,
            'estimator': estimator,
            'coefficients': coefficients,
            'version': version,
            'metadata': metadata
            }
    res = req.put(url + 'model/' + name, json=data)

def delete_model(modelname, version=None):
    version_text = ""
    if version != None:
        version_text = "?version=" + version
    res = req.delete(url + '/model/' + modelname + version_text)
    print(res.text)

def main_function():
    # Get the key from the database
    database = 'ml_fingerprint_database.db'
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    db_key = c.execute('select * from key order by id desc limit 1').fetchone()
    public_key = RSA.import_key(db_key['publickey'])
    private_key = RSA.import_key(db_key['privatekey'])

    # Decorate BaseEstimator
    main.decorate_base_estimator()

    modelname = 'example_regression'
    model = example_models.vanderplas_regression()
    model.sign(private_key)

    insert_model(model, modelname, True, "regression", {"MSE":0.987}, "1.2.78", {"parameter_X":"TEST"})
    
    #update_model(model, "example_regression", True, "regression", {"MSE":0.987}, "1.2.78", {"parameter_X":"TEST"})
    server_model = get_model(modelname, public_key)
    print(server_model.coef_)
    delete_model(modelname)


if __name__ == '__main__':
    main_function()
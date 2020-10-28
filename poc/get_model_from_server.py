from ml_fingerprint import main
#from sklearn.linear_model import LinearRegression
from Crypto.PublicKey import RSA
import sqlite3
import pickle
import requests as req

#Get the key from the database
database = 'ml_fingerprint_database.db'
conn = sqlite3.connect(database)
conn.row_factory = sqlite3.Row
c = conn.cursor()
db_key = c.execute('select * from key order by id desc limit 1').fetchone()
public_key = RSA.import_key(db_key['publickey'])


main.decorate_base_estimator()

modelname = 'example_unaltered'
res = req.get('http://localhost:5000/getmodel?modelname=' + modelname)
if res.status_code != 200:
    print(res.text)
else:
    model = pickle.loads(res.content)
    if main.isInyected(model):
        model.verify(public_key)
    else:
        print(model.coef_)
from ml_fingerprint import main
import numpy as np
from sklearn.linear_model import LinearRegression
from Crypto.PublicKey import RSA
import sqlite3
import pickle
import joblib
from poc import example_models


#Get the key from the database
database = 'ml_fingerprint_database.db'
conn = sqlite3.connect(database)
conn.row_factory = sqlite3.Row
c = conn.cursor()
db_key = c.execute('select * from key order by id desc limit 1').fetchone()
key = RSA.import_key(db_key['privatekey'])
public_key = RSA.import_key(db_key['publickey'])

model = example_models.vanderplas_regression()

print(main.isInyected(model))

#Adding the verification methods to the BaseEstimator class
main.decorate_base_estimator()

#Signing the model after it has been trained
model.sign(key)



#Insert the serialized model into the DB
c.execute('delete from models')

#Serialize model with pickle
serialized_model = pickle.dumps(model)
modelname = 'example_unaltered'
c.execute('insert into models (name, model) values (?,?)', (modelname, serialized_model))

#Serialize model with joblib
serialized_model = joblib.dump(model, 'model.joblib')

conn.commit()
conn.close()



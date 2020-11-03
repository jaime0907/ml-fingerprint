from ml_fingerprint import main
import numpy as np
from sklearn.linear_model import LinearRegression
from Crypto.PublicKey import RSA
import sqlite3
import pickle
import joblib


#Get the key from the database
database = 'ml_fingerprint_database.db'
conn = sqlite3.connect(database)
conn.row_factory = sqlite3.Row
c = conn.cursor()
db_key = c.execute('select * from key order by id desc limit 1').fetchone()
key = RSA.import_key(db_key['privatekey'])
public_key = RSA.import_key(db_key['publickey'])

#Create the model
model = LinearRegression()
# Create some data for the regression
rng = np.random.RandomState(1)
X = rng.randn(200, 2)
y = np.dot(X, [-2, 1]) + 0.1 * rng.randn(X.shape[0])
# fit the regression model
model.fit(X, y)
# create some new points to predict
X2 = rng.randn(100, 2)
# predict the labels
y2 = model.predict(X2)

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



from ml_fingerprint import main
import numpy as np
from sklearn.linear_model import LinearRegression
from Crypto.PublicKey import RSA

#Test to check if the decorator works when using ml-fingerprint as a package.
#NOTE: It requires having the ml-fingerprint installed.

#This test recreates the 2D linear regression model in VanderPlas' book, adds the decorator and tests if it has the foo() method.

#Generate the RSA key used to sign and verify the model
key = RSA.generate(2048)
public_key = key.publickey()

#Create the model
model = LinearRegression()

#Signing the model BEFORE it has been trained
model.sign(key)

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

#Adding the verification methods to the BaseEstimator class
main.decorate_base_estimator()

#Checking if it works
model.hello_world()

#Verifying the model (that has been signed before training, and therefore, should not verify)
model.verify(public_key)
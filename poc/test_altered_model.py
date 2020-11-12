from ml_fingerprint import main
import numpy as np
from sklearn.linear_model import LinearRegression
from Crypto.PublicKey import RSA
import pickle
import example_models

# Test to check if the decorator works when using ml-fingerprint as a package.
# NOTE: It requires having the ml-fingerprint installed.

# This test gets a model, adds the fingerprint methods, signs the model, MODIFIES IT and then tries to verify it.

# Generate the RSA key used to sign and verify the model
key = RSA.generate(2048)
public_key = key.publickey()

# Get a model from the example_models.py file
model = example_models.vanderplas_regression()

# Adding the verification methods to the BaseEstimator class
main.decorate_base_estimator()
# Signing the model BEFORE it has been trained
model.sign(key)

# Modifying the model
model.__dict__['coef_'][0] = -4.0

# Checking if it works
model.hello_world()

# Verifying the model (that has been signed before training, and therefore, should not verify)
model.verify(public_key)



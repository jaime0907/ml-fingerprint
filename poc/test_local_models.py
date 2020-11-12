from ml_fingerprint import main
import numpy as np
from sklearn.linear_model import LinearRegression
from Crypto.PublicKey import RSA
import pickle
import example_models

# Tests to check if the decorator works when using ml-fingerprint as a package.
# NOTE: It requires having the ml-fingerprint installed.

def unaltered_test(model, key):
    # This test gets a model, adds the fingerprint methods, signs the model and then tries to verify it.
    print("Starting unaltered test...")

    # Adding the verification methods to the BaseEstimator class
    main.decorate_base_estimator()

    # Checking if it works
    model.hello_world()

    # Signing the model after it has been trained
    model.sign(key)

    # Verifying the model
    model.verify(key.publickey())
    print()


def altered_test(model, key):
    # This test gets a model, adds the fingerprint methods, signs the model, MODIFIES IT and then tries to verify it.
    print("Starting altered test...")

    # Adding the verification methods to the BaseEstimator class
    main.decorate_base_estimator()
    # Signing the model BEFORE it has been trained
    model.sign(key)

    # Modifying the model
    if type(model).__name__ == 'SVC':
        model.__dict__['dual_coef_'][0][0] = -4.0
    elif type(model).__name__ == 'LinearRegression':
        model.__dict__['coef_'][0] = -4.0
    else:
        print("altered_test() failed. The given model isn't compatible with this test.")
        return

    # Checking if it works
    model.hello_world()

    # Verifying the model (that has been signed before training, and therefore, should not verify)
    model.verify(key.publickey())
    print()

def unsigned_test(model, key):
    # This test gets a model, adds the fingerprint methods, DOESN'T sign the model and then tries to verify it.
    print("Starting unsigned test...")

    # Adding the verification methods to the BaseEstimator class
    main.decorate_base_estimator()

    # Checking if it works
    model.hello_world()

    # Verifying the model
    model.verify(key.publickey())
    print()



def main_function():
    # Generate the RSA key used to sign and verify the model
    key = RSA.generate(2048)

    # Get a model from the example_models.py file
    model = example_models.vanderplas_regression()
    ### model = example_models.vanderplas_classifier()

    # Do all the tests
    unsigned_test(model, key)
    unaltered_test(model, key)
    altered_test(model, key)
    

if __name__ == '__main__':
    main_function()
from sklearn import base
from functools import wraps # This convenience func preserves name and docstring
import orjson
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from copy import deepcopy

# Function taken from Michael Garod
# This function is used by decorate_base_estimator to add a method to an existing class without having to modify said class' source code (maybe this function should be private?)
def add_method(cls):
    def decorator(func):
        @wraps(func) 
        def wrapper(self, *args, **kwargs): 
            return func(*args, **kwargs)
        setattr(cls, func.__name__, wrapper)
        # Note we are not binding func, but wrapper which accepts self but does exactly the same as func
        return func # returning func means func can still be used normally
    return decorator

#This function should be called by the user on their code. It adds the foo() method to scikit's BaseEstimator class, making foo() avaliable in all scikit's estimators.
def decorate_base_estimator():
    baseClass = base.BaseEstimator

    @add_method(baseClass) # Adding foo method to scikit's BaseEstimator class.
    def hello_world():
        print('Hello world!')

    # Takes a RSA key and signs the serialized model with it.
    def sign(self, private_key):
        print("Signing model...")
        # Make a copy of the model and delete the signature so the signature doesn't affect the hash.
        # This is necessary because when adding the signature we are modifying the model, so the hash done when verifying won't be the same as the one used to sign the model.
        modelcopy = deepcopy(self)
        if hasattr(modelcopy, 'signature'):
            del modelcopy.signature

        # Serializes the model parameters using orjson, which provides native numpy compatibility
        serialized_model = orjson.dumps(modelcopy.__dict__, option=orjson.OPT_SERIALIZE_NUMPY)

        # Hashes the serialized model using SHA256 algorithm
        hashed_model = SHA256.new(serialized_model)

        # Signs the hashed model with the provided private key and then adds the signature to the model object
        signature = pkcs1_15.new(private_key).sign(hashed_model)
        self.signature = signature
        return self.signature

    # Manually add the sign() method, because it need access to self
    setattr(baseClass, sign.__name__, sign)

    def verify(self, public_key):
        print("Validating model...")
        # Make a copy of the model and delete the signature so the hash fits the one generated in sign()
        modelcopy = deepcopy(self)
        if hasattr(modelcopy, 'signature'):
            del modelcopy.signature

        # Serializes the model parameters using orjson, which provides native numpy compatibility
        serialized_model = orjson.dumps(modelcopy.__dict__, option=orjson.OPT_SERIALIZE_NUMPY)

        # Hashes the serialized model using SHA256 algorithm
        hashed_model = SHA256.new(serialized_model)

        # Tries to verify the model with its signature and the public key provided.
        try:
            pkcs1_15.new(public_key).verify(hashed_model, self.signature)
            print("The signature is valid")
            return True
        except (ValueError, TypeError):
            raise Exception("The signature is NOT valid.")
        except AttributeError:
            raise Exception("This model has not been signed.")

    # Manually add the verify() method, because it need access to self
    setattr(baseClass, verify.__name__, verify)

# Function used to check if a scikit model has been inyected with ml-fingerprint methods
def isInyected(model):
    return bool(getattr(model, 'sign', False))
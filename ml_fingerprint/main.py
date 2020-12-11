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

def decorate_base_estimator():
    '''
    This function should be called by the user on their code.
    It adds the sign and verification methods to scikit's BaseEstimator class, making them avaliable in all scikit's estimators.
    '''
    baseClass = base.BaseEstimator

    @add_method(baseClass) # Adding foo method to scikit's BaseEstimator class.
    def hello_world():
        print('Hello world!')

    def sign(self, private_key):
        '''
        Takes a RSA private key and signs the model with it.

        Parameters
        ----------
        private_key : Crypto.PublicKey.RSA.RsaKey
            The private key you want to sign the model with.
        '''
        print("Signing model...")

        self.ml_fingerprint_data = {}

        # Make a copy of the model and delete all ml-fingerprint extra data (the signature and the excluded attributes) so they don't affect the hash.
        # This is necessary because when adding our data we are modifying the model, so the hash done when verifying won't be the same as the one used to sign the model.
        modelcopy = deepcopy(self)
        if hasattr(modelcopy, 'ml_fingerprint_data'):
            del modelcopy.ml_fingerprint_data

        # Checks for any attribute not compatible with orjson (mainly numpy arrays with non-standard data in them).
        # If any attribute cannot be json serialized, it excludes it from the serialization.
        self.ml_fingerprint_data['excluded_data'] = []
        for k in modelcopy.__dict__:
            try:
                orjson.dumps(modelcopy.__dict__[k], option=orjson.OPT_SERIALIZE_NUMPY)
            except TypeError:
                self.ml_fingerprint_data['excluded_data'].append(k)
        
        for elem in self.ml_fingerprint_data['excluded_data']:
            delattr(modelcopy, elem)

        # Serializes the model parameters using orjson, which provides native numpy compatibility
        serialized_model = orjson.dumps(modelcopy.__dict__, option=orjson.OPT_SERIALIZE_NUMPY)

        # Hashes the serialized model using SHA256 algorithm
        hashed_model = SHA256.new(serialized_model)

        # Signs the hashed model with the provided private key and then adds the signature to the model object
        signature = pkcs1_15.new(private_key).sign(hashed_model)
        self.ml_fingerprint_data['signature'] = signature
        return signature

    # Manually add the sign() method, because it need access to self
    setattr(baseClass, sign.__name__, sign)

    def verify(self, public_key):
        '''
        Takes a RSA public key and verifies the model with it.

        Parameters
        ----------
        public_key : Crypto.PublicKey.RSA.RsaKey
            The public key you want to verify the model with.
        '''
        print("Validating model...")

        if not hasattr(self, 'ml_fingerprint_data'):
            raise Exception("This model has not been signed.")

        # Make a copy of the model and delete ml-fingerprint data so the hash fits the one generated in sign()
        modelcopy = deepcopy(self)
        if hasattr(modelcopy, 'ml_fingerprint_data'):
            del modelcopy.ml_fingerprint_data

        # Deleting all excluded attributes from the copy so it won't serialize them.
        for elem in self.ml_fingerprint_data['excluded_data']:
            delattr(modelcopy, elem)

        # Serializes the model parameters using orjson, which provides native numpy compatibility
        serialized_model = orjson.dumps(modelcopy.__dict__, option=orjson.OPT_SERIALIZE_NUMPY)

        # Hashes the serialized model using SHA256 algorithm
        hashed_model = SHA256.new(serialized_model)

        # Tries to verify the model with its signature and the public key provided.
        try:
            pkcs1_15.new(public_key).verify(hashed_model, self.ml_fingerprint_data['signature'])
            print("The signature is valid")
            return True
        except (ValueError, TypeError):
            raise Exception("The signature is NOT valid.")
        except AttributeError:
            raise Exception("This model has not been signed.")

    # Manually add the verify() method, because it need access to self
    setattr(baseClass, verify.__name__, verify)

def isInyected(model):
    '''
    Function used to check if a scikit model has been inyected with ml-fingerprint methods

    Parameters
    ----------
    model : any sklearn estimator
        The scikit-learn model you want to check if is inyected with sign() and verify() methods.

    Returns
    -------
    bool
        True if the model has been previously inyected, False otherwise.

    '''
    return bool(getattr(model, 'sign', False))
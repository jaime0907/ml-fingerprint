from sklearn import base
from functools import wraps # This convenience func preserves name and docstring
import pickle
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

#Function taken from Michael Garod
#This function is used by decorate_base_estimator to add a method to an existing class without having to modify said class' source code (maybe this function should be private?)
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
    @add_method(baseClass) #Adding foo method to scikit's BaseEstimator class.
    def hello_world():
        print('Hello world!')

    #Takes a RSA key and signs the serialized model with it.
    def sign(self, key):
        print("Signing model...")
        serialized_model = pickle.dumps(self)
        hashed_model = SHA256.new(serialized_model)
        signature = pkcs1_15.new(key).sign(hashed_model)
        setattr(self.__class__, "signature", signature) #Sets the signature as an attribute for the model
        return self.signature
    #Manually add the sign() method, because it need access to self
    setattr(baseClass, sign.__name__, sign)

    def verify(self, public_key):
        print("Validating model...")
        serialized_model = pickle.dumps(self)
        hashed_model = SHA256.new(serialized_model)
        try:
            pkcs1_15.new(public_key).verify(hashed_model, self.signature)
            print("The signature is valid")
        except (ValueError, TypeError):
            print("The signature is NOT valid.")
        except AttributeError:
            print("This model has not been signed.")
    #Manually add the verify() method, because it need access to self
    setattr(baseClass, verify.__name__, verify)

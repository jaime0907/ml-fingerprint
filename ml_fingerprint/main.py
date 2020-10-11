from sklearn import base
from functools import wraps # This convenience func preserves name and docstring

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
    @add_method(base.BaseEstimator) #Adding foo method to scikit's BaseEstimator class.
    def foo():
        print('Hello world!')

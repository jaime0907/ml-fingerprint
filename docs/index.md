## ml-fingerprint

This package adds integrity verification to [_scikit-learn_](scikit-learn.org) models.

### How it works

_ml-fingerprint_ adds two methods into all _scikit-learn_ models: `sign(private_key)` and `verify(public_key)`.

`sign(private_key)` takes the current state of the model and generates a signature signed with the private key given.
`verify(public_key)` decrypts the existing signature of the model, compares it to the current state of the model and returns `True` if the signature is valid (and therefore the model hasn't been changed since it was signed)

To add both methods into all existing scikit-learn models, the user has to call `decorate_base_estimator()` before using either `sign()` or `verify()`.

### Under the hood

`decorate_base_estimator()` uses Python's built-in function `setattr(object, name, value)`. Seeing this may raise some eyebrows, as it takes an object and assigns to it a value with the name provided. However, _everything_ is an object in Python, including classes and functions (usually called _first class objects_). That means that we can use a function as the `value` (in this case `sign()` and `verify()`) and a class as the `object`.

The next question could be: what class? There are dozens of estimators in _scikit-learn_, and adding both methods to all of them would be highly unefficient. Thankfully, the devs at _scikit-learn_ have solved this problem for us, as all estimators inherit from a base class: [_sklearn.base.BaseEstimator_](https://scikit-learn.org/stable/modules/generated/sklearn.base.BaseEstimator.html). That way, we can add both `sign()` and `verify()` to the _BaseEstimator_ class, and that will make them avaliable in all existing _scikit-learn_ models.


```python
def decorate_base_estimator():
    baseClass = sklearn.base.BaseEstimator
    
    def sign(self, key):
        #sign() code
        
    setattr(baseClass, sign.__name__, sign)

    def verify(self, public_key):
        #verify() code
        
    setattr(baseClass, verify.__name__, verify)
    
```

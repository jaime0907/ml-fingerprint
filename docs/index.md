## ml-fingerprint

This package adds integrity verification to [_scikit-learn_](scikit-learn.org) models.

### How it works

_ml-fingerprint_ adds two methods into all _scikit-learn_ models: `sign(private_key)` and `verify(public_key)`.

`sign(private_key)` takes the current state of the model and generates a signature signed with the private key given.
`verify(public_key)` decrypts the existing signature of the model, compares it to the current state of the model and returns `True` if the signature is valid (and therefore the model hasn't been changed since it was signed)

To add both methods into all existing scikit-learn models, the user has to call `decorate_base_estimator()` before using either `sign()` or `verify()`.

### Under the hood

`decorate_base_estimator()` uses Python's built-in function `setattr(object, name, value)`. This may raise some eyebrows, as `setattr()` takes an `object` and assigns to it a `value` with the provided `name`. However, _everything_ is an object in Python, including classes and functions (usually called _first class objects_). That means that we can use a function as the `value` (in this case `sign()` and `verify()`) and a class as the `object`.

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

Now, let's take a closer look at `sign()` and `verify()`:

```python
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
    except (ValueError, TypeError):
        print("The signature is NOT valid.")
    except AttributeError:
        print("This model has not been signed.")
```

Both methods start doing the same work. First we make a [_deepcopy_](https://docs.python.org/3/library/copy.html) of the model, in order to delete the signature without modifying the original model. This is needed because we calculate the signature using a hash of the parameters of the model, but the signature itself is a parameter of the model, so if we calculate the hash and then add the new signature, the model itself will change, and the verification will fail.

After we make sure that the signature has been deleted from `modelcopy`, we serialize the model into a string using [_orjson_](https://github.com/ijl/orjson), a JSON library that works natively with numpy arrays (which are used by _scikit-learn_).

Then, we calculate a hash of our serialized string using [_PyCryptodome_](https://pypi.org/project/pycryptodome/), a Python package that implements low-level cryptographic primitives. The hash algorithm used is [SHA256](https://en.wikipedia.org/wiki/SHA-2), which provides a great balance between security and speed.

At this point is where our `sign()` and `verify()` methods begin to differ.

`sign()` takes the hash and the `private_key` and creates a [PKCS #1 v1.5 signature](https://tools.ietf.org/html/rfc2313), using again _PyCryptodome_. This signature is then appended to the original model (`self`). 

`verify()` takes the `public_key`, the hash of the model and the signature of the model, and verifies not only that the model hasn't been modified since the time it was signed, but also that it was signed using the private counterpart of the public key you used, which means that if you trust the public key (i.e. it is signed by a [CA](https://en.wikipedia.org/wiki/Certificate_authority)), you can trust the model.

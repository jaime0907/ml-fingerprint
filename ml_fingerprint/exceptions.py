class ModelNotSigned(Exception):
    """
    Exception raised when trying to verify a model that hasn't been signed, 
    or has got its signature deleted.
    """
    pass

class VerificationError(Exception):
    """
    Exception raised when the verification has failed.
    This could be because the signature doesn't fit the model (i.e. the model
    has been modified since the signature), or because the public key used
    to decrypt the model isn't the counterpart of the private key used to
    sign it.
    """
    pass
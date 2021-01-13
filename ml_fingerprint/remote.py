from . import ml_fingerprint, example_models, exceptions
from Crypto.PublicKey import RSA
import sqlite3
import pickle
import requests as req
import json
import base64

class RemoteServer():
    """
    Class that allows to easily manage models from a server.

    Attributes
    ----------
    url : str
        URL of the API of the remote server.
    """
    def __init__(self, url):
        if not url.endswith('/'):
            url += "/"
        self.url = url

    
    
    def insert_model(self, model, name, supervised, model_type, scores, version, metadata, date, description, owner):
        '''
        Takes a model and all its metadata, and uploads it to the server.

        Parameters
        ----------
        model : any sklearn estimator
            The model to be inserted.
        name : str
            The name of the model.
        supervised : bool
            True if the model belongs to "supervised learning" category.
            False if belongs to "unsupervised learning" category.
        model_type : str
            The category of the model (i.e. regression, classification, clustering...).
        scores : dict
            Dictionary with the scores of the model, following this syntaxis: {"score_name" : score_value} 
        version : str
            The version of the model.
        metadata : dict
            Dictionary with any additional data you want to store alongside the model.
        date : datetime.datetime
            Datetime object with the date and time of the creation of the model (usually datetime.now())
        description : str
            Description of the model.
        owner : str
            Owner(s) of the model.
        Returns
        -------
        requests.Response
            Response object returned by the server after the POST petition.
        '''

        b64string_model, serializer_bytes, serializer_text = encode_model(model)

        estimator = type(model).__name__
        
        supervised_int = 0
        if supervised:
            supervised_int = 1
        date_str = date.isoformat()
        data = {'name': name,
                'serialized_model': b64string_model,
                'serializer_bytes': serializer_bytes,
                'serializer_text': serializer_text,
                'supervised': supervised_int,
                'type': model_type,
                'estimator': estimator,
                'scores': scores,
                'version': version,
                'metadata': metadata,
                'date': date_str,
                'description': description,
                'owner': owner
                }
        res = req.post(self.url + 'model/' + name, json=data)

    def get_model(self, modelname, public_key, version=None):
        '''
        Retrieves a model from the server, and verifies its integrity and authenticity
        before returning it.

        Parameters
        ----------
        modelname : str
            The name of the model to be retrieved.
        public_key : Crypto.PublicKey.RSA.RsaKey
            The public key whose private counterpart was used to sign the model.
            This is needed to verify the integrity and authenticity of the model.
        version : str, optional
            The version of the model to be retrieved. If not given, it will retrieve
            the last version.

        Returns
        -------
        (any sklearn estimator)
            The received model from the server.
        '''

        version_text = ""
        if version != None:
            version_text = "?version=" + version
        res = req.get(self.url + 'model/' + modelname + version_text)
        if res.status_code != 200:
            print(res.text)
        else:
            data = res.json()
            model = decode_model(data['serialized_model'])
            if ml_fingerprint.isInyected(model):
                signIsGood = model.verify(public_key)
                if signIsGood:
                    return model
                else:
                    raise exceptions.VerificationError("Sign verification failed.")
                
            else:
                return model

    def update_model(self, model, name, supervised, model_type, scores, version, metadata, date, description, owner):
        '''
        Takes a model that is already present on the server and updates the model itself
        and all its metadata.

        .. note:: This method is NOT intended to upload a new version of the same model.
            In order to do that, use insert_model() instead.

        Parameters
        ----------
        model : any sklearn estimator
            The model to be updated.
        name : str
            The name of the model. Has to be the same as the model to be updated.
        supervised : bool
            True if the model belongs to "supervised learning" category.
            False if belongs to "unsupervised learning" category.
        model_type : str
            The category of the model (i.e. regression, classification, clustering...).
        scores : dict
            Dictionary with the scores of the model, following this syntaxis: {"score_name" : score_value} 
        version : str
            The version of the model. Has to be the same as the one to be updated.
        metadata : dict
            Dictionary with any additional data you want to store alongside the model.

        Returns
        -------
        requests.Response
            Response object returned by the server after the PUT petition.
        '''

        b64string_model, serializer_bytes, serializer_text = encode_model(model)

        estimator = type(model).__name__
        
        supervised_int = 0
        if supervised:
            supervised_int = 1
            
        date_str = date.isoformat()

        data = {'name': name,
                'serialized_model': b64string_model,
                'serializer_bytes': serializer_bytes,
                'serializer_text': serializer_text,
                'supervised': supervised_int,
                'type': model_type,
                'estimator': estimator,
                'scores': scores,
                'version': version,
                'metadata': metadata,
                'date': date_str,
                'description': description,
                'owner': owner
                }
        res = req.put(self.url + 'model/' + name, json=data)

    def delete_model(self, modelname, version=None):
        '''
        Deletes a model from the server.

        Parameters
        ----------
        modelname : str
            The name of the model to be deleted.
        version : str, optional
            The version of the model to be deleted. If not given, it will delete
            the last version.

        Returns
        -------
        requests.Response
            Response object returned by the server after the PUT petition.
        '''

        version_text = ""
        if version != None:
            version_text = "?version=" + version
        res = req.delete(self.url + 'model/' + modelname + version_text)
        print(res.text)


def encode_model(model):
    pickled_model = pickle.dumps(model)
    b64bytes_model = base64.b64encode(pickled_model)
    b64string_model = b64bytes_model.decode('ascii')

    serializer_bytes = "pickle"
    serializer_text = "base64"

    return b64string_model, serializer_bytes, serializer_text

def decode_model(data):
    pickled_model = base64.b64decode(data)
    model = pickle.loads(pickled_model)
    return model


def put_key_in_db(private_key, public_key):
    database = 'ml_fingerprint_database.db'
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('delete from key')
    c.execute('insert into key (privatekey, publickey) values (?,?)', (private_key.export_key(), public_key.export_key()))
    conn.commit()
    conn.close()
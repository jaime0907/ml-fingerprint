from requests import api
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
    def __init__(self, url, api_key, unsafe_https=False):
        if not url.endswith('/'):
            url += "/"
        self.url = url
        self.api_key = api_key
        self.unsafe_https = unsafe_https

    
    
    def insert_model(self, model, name, supervised, model_type, scores, version, metadata, date, description):
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
                'api_key': self.api_key
                }
        res = req.post(self.url + 'model/' + name, json=data, verify=not self.unsafe_https)
        if res.status_code != 200:
            print("ERROR: ", res.text)

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

        params = {}
        params['api_key'] = self.api_key
        if version != None:
            params['version'] = version
        res = req.get(self.url + 'model/' + modelname, params=params, verify=not self.unsafe_https)
        if res.status_code != 200:
            print("ERROR: ", res.text)
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

    def update_model(self, model, name, supervised, model_type, scores, version, metadata, date, description):
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
        date : datetime.datetime
            Datetime object with the date and time of the creation of the model (usually datetime.now())
        description : str
            Description of the model.

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
                'api_key': self.api_key
                }
        res = req.put(self.url + 'model/' + name, json=data, verify=not self.unsafe_https)
        if res.status_code != 200:
            print("ERROR: ", res.text)

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

        params = {}
        params['api_key'] = self.api_key
        if version != None:
            params['version'] = version
        res = req.delete(self.url + 'model/' + modelname, params=params, verify=not self.unsafe_https)
        if res.status_code != 200:
            print("ERROR: ", res.text)
        else:
            print(res.text)

    def get_list_models(self, modelname=None, type_str=None, allversions=False, doprint=False):
        '''
        Retrieves the list of models from the server, filtering by the given parameters.

        Parameters
        ----------
        modelname : str, optional
            If specified, it will show all versions of that model.
        type_str : str, optional
            If specified, it will filter by that model type.
            If type is "supervised" or "unsupervised", it will filter by that instead.
        allversions : bool, optional
            If True, it will show all versions of all models in the list.
            If False, it will show only the lastest version for each model.
        doprint : bool, optional
            If True, pretty prints the list of models.
        Returns
        -------
        list
            List containing objects with all the metadata of the models.
        '''

        params = {}
        params['api_key'] = self.api_key
        params['format'] = "json"
        modelname_str = ""
        if modelname != None:
            modelname_str = "/" + modelname
        if type_str != None:
            params['type'] = type_str
        if allversions:
            params['allversions'] = "true"
        res = req.get(self.url + 'modellist' + modelname_str, params=params, verify=not self.unsafe_https)
        if res.status_code != 200:
            print("ERROR: ", res.text)
        else:
            data = res.json()
            if doprint:
                for model in data:
                    print("--", model['name'], "--")
                    for col in model.keys():
                        if col == "name":
                            continue
                        print(str(col) + ": " + str(model[col]))
            return data

def encode_model(model):
    '''
    Takes a model, serializes it to bytes using pickle, and then
    converts it into a base64 string.

    Parameters
    ----------
    model : any sklearn estimator
        The model to be serialized.

    Returns
    -------
    b64string_model : str
        Base64 string that represents the serialized model.
    serializer_bytes : str
        Name of the package used to serialize the model into bytes.
        In this case, it is always 'pickle'.
    serializer_text : str
        Name of the package used to convert the serialized bytes into text.
        In this case, it is always 'base64'.
    '''
    pickled_model = pickle.dumps(model)
    b64bytes_model = base64.b64encode(pickled_model)
    b64string_model = b64bytes_model.decode('ascii')

    serializer_bytes = "pickle"
    serializer_text = "base64"

    return b64string_model, serializer_bytes, serializer_text

def decode_model(data):
    '''
    Takes a base64 string, converts it into bytes, and then
    decodes it into a Python object (the model) using pickle.

    Parameters
    ----------
    data : str
        Base64 string that represents the serialized model.
    
    Returns
    -------
    model : any sklearn estimator
        The model deserialized.
    '''
    pickled_model = base64.b64decode(data)
    model = pickle.loads(pickled_model)
    return model


def put_key_in_db(private_key, public_key):
    '''
    Deletes from the database the current key stored,
    and inserts the new pair of keys provided.

    Used only for test purposes. The private key should not
    be stored in plain text in a SQL database.

    Parameters
    ----------
    private_key : Crypto.PublicKey.RSA.RsaKey
        The private half of the key.

    public_key : Crypto.PublicKey.RSA.RsaKey
        The public half of the key.
    '''
    database = 'ml_fingerprint_database.db'
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute('delete from key')
    c.execute('insert into key (privatekey, publickey) values (?,?)', (private_key.export_key(), public_key.export_key()))
    conn.commit()
    conn.close()
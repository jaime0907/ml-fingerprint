import unittest
from ml_fingerprint import ml_fingerprint, example_models, exceptions
from Crypto.PublicKey import RSA

class VerificationTestCase(unittest.TestCase):
    def setUp(self):
        self.model = example_models.vanderplas_regression()
        self.private_key = RSA.import_key('''-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAnB5U96c2cR7C/2BaBd7tSgNMQAODRay0n4AVJRw2WyuP828T
w18lK3yapnWfwxTMMv7machk7eyWRvrmp84fzdZqeebetHEOdWhQGJhghs15fnFA
a1NHDcpFbbH6JoLhZyL0BPNZvQdIXcrGdL/eGCGKvMWr8OjV8Q1W1v1Oc7rggMwm
WggM9XCgQGACXQROJfs4+cowVvqxJeSJ9ucp/UmaQoaBRP8ncf6uUAfoHreWEH1n
qQqoQ5TYqw4/QqnK6owCWwaHOWFsB+e8AkqpVLfcsrXeCOdYKNFUtmhmfWzHFmKs
MWqrMOkewSnWYix48EnewXXpEDi2Ip9437cDTwIDAQABAoIBAAHwsjMW0fEeUqGX
zxQuoUKBrDpwKfM/LgxV5mG89cd+WL1nCaKRWYnRfCKMItWszUhEuOYNmOlWAMdj
mHLcGpPfCeLgIt48UAIc7Ve5JsYTsAVXDcRi2TwfyoJQQLki5Peyn8/NwdRrZdeC
JB9S1z1oFJUkYAI+xHrf9krPiFEJ7dJwSWBk1G/0HMS2+aUXiyNqB+oKvhNK2uTL
ZSRJJl0rrhruNvST9RDsqj6aEAyHpOsxNE919Bvj2XqNpetFIOlPOGSqd6M8Xpgq
Jv6sTtIIGchCB2LmCHHKfFlu2WdLSy8YtuTT5GE3crTqu3J+6REkt6051xwDhixK
fXdGBBECgYEAvYfZ9nygXcuXRPjYElq4TnPv1Ue6lis+/UAphc+ElGJMhNhvK3g9
Zqc+JZCXF2wBVvx+JYtw1QOSnHSN9sNDT3k/p3WE96jgO/goHIlrLhTKHt3lAnOp
0JyTCnsgBgVTVDvylkwW1wyMr0gmwAkKlNx12s0fROBaSj+lJ+/1kU0CgYEA0t64
LwDY+WsDtEiBxFPVjkMiqz1oZBlEm1bKgQteGBrZ14qtw15PNXT2qoErBkmLGio1
K8WHyaQufnjgLhLkPns4MwspiPi4PFUoN/xqi9R4IlXp1BwoHYTiPTCBVlP97Mcd
rrLd/iibIYErglnqT1g+bqp3OV4mPBf0TAA+WQsCgYBNr9Swyw60w5HCrLlsdJEd
XzpMUvVxPlK4XcdnWNNAOzagMVMIH2YToLPBlA3KhPPbou1WGFzsg2ViCghywEDj
35Au5OXW2frnueU/JTiwj8b1dgC7y4ssvjErV6KdtSsd2OCrqI6oITW9VzbC+jHD
KMaKJBAQHGIGEyZwQ1SF9QKBgCCQpq8TmW6DWVIZNHkmXT+YHJ2HYTy8Lj0zHRjq
sYBVfTjtQMKAKQlfY8yXIBbberDyvb1hxwOb6FY9wpk676a6jsZLPgHaL1GZ8Rkc
UTQA/wCGdhL8ujE82VeLyx2S4Q8U/P+CvgfHK5X0Bc0ep7HTNekPSFRCtvLm3CJ0
kyxbAoGBAKf7ngLFzGWqjszoFsU2cLOOToWXrGJKGx5HSYp9lcOF8ADFCpWkMSgn
BZkzaa3IKIKoHOhyf4aOHif1uqBbF1tAMJ+Q6LJ4XDoeIeylWlZW2rNLw9ETfPow
f2sFc2oi0MN86k7DSB22XGo5ifJTZAp9KLZIOjh1AW+5WUJHnNhy
-----END RSA PRIVATE KEY-----''')
        self.public_key = RSA.import_key('''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnB5U96c2cR7C/2BaBd7t
SgNMQAODRay0n4AVJRw2WyuP828Tw18lK3yapnWfwxTMMv7machk7eyWRvrmp84f
zdZqeebetHEOdWhQGJhghs15fnFAa1NHDcpFbbH6JoLhZyL0BPNZvQdIXcrGdL/e
GCGKvMWr8OjV8Q1W1v1Oc7rggMwmWggM9XCgQGACXQROJfs4+cowVvqxJeSJ9ucp
/UmaQoaBRP8ncf6uUAfoHreWEH1nqQqoQ5TYqw4/QqnK6owCWwaHOWFsB+e8Akqp
VLfcsrXeCOdYKNFUtmhmfWzHFmKsMWqrMOkewSnWYix48EnewXXpEDi2Ip9437cD
TwIDAQAB
-----END PUBLIC KEY-----''')
        ml_fingerprint.decorate_base_estimator()

    def test_signed_model(self):
        self.model.sign(self.private_key)
        self.assertTrue(self.model.verify(self.public_key))

    def test_unsigned_model(self):
        with self.assertRaises(exceptions.ModelNotSigned):
            self.model.verify(self.public_key)
    
    def test_altered_model(self):
        self.model.sign(self.private_key)
        self.model.__dict__['coef_'][0] = -4.0
        with self.assertRaises(exceptions.VerificationError):
            self.model.verify(self.public_key)

if __name__ == '__main__':
    unittest.main()
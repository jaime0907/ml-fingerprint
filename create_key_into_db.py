from Crypto.PublicKey import RSA
import sqlite3

database = 'ml_fingerprint_database.db'
conn = sqlite3.connect(database)
conn.row_factory = sqlite3.Row
c = conn.cursor()

key = RSA.generate(2048)
public_key = key.publickey()

c.execute('insert into key (privatekey, publickey) values (?,?)', (key.export_key(), public_key.export_key()))
conn.commit()
conn.close()
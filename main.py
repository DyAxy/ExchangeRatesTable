import os
import io
import json
import pymongo
import requests
import paramiko
from sshtunnel import SSHTunnelForwarder


try: 
    # Pull Data via APILayer
    url = "https://api.apilayer.com/exchangerates_data/latest?base=USD"
    payload = {}
    headers= {
      "apikey": os.environ["APIKEY"]
    }
    r = requests.get(url, headers=headers, data = payload)
    
    data = r.json()
    
    # Export Data to file
    with open('data.json', 'w', encoding='utf-8') as file:
        file.write(json.dumps(data))

    # Update Data to database
    with SSHTunnelForwarder(
        ssh_address_or_host=os.environ['SSHIP'],
        ssh_username='root',
        ssh_pkey=paramiko.RSAKey.from_private_key(io.StringIO(os.environ['SSHKEY'])),
        remote_bind_address= ('127.0.0.1', 27017)
    ) as ssh:
        ssh.start()
        mongoClient = pymongo.MongoClient(host='127.0.0.1',port=ssh.local_bind_port)
        myCol = mongoClient["daily"]["exchange"]

        if data['success'] is not True:
            raise Exception("Data Error")

        updateTime = {'updateTime':data['timestamp']}
        if myCol.find_one(updateTime) is not None:
            raise Exception("Data duplicated")

        r = myCol.insert_one(data['rates'])
        myCol.update_one({'_id':r.inserted_id}, { "$set": updateTime })
    

except Exception as error:
    print(error)
    exit(1)

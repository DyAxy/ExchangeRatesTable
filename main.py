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

    uri = os.environ["MONGOURI"]
    # Update Data to database
    with pymongo.MongoClient(uri) as mongoClient:
        myCol = mongoClient["api"]["rate"]

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

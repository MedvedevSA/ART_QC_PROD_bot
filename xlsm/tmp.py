import xlwings as xw
import redis
from dotenv import dotenv_values
import json
import os

def main():
    config = dotenv_values(".env")
    r = redis.Redis(host=config['HOST'], port=6379, db=0)
    
    #name='test:push'
    r_user = "listener:list"
    r_meas_list = "QC:meas:list" 
    
    res = r.lrange(r_meas_list, 0 , -1)



    print(int(b'123'.decode('utf-8')))
    #listeners_id = r.lrange(r_user,0,-1)
    #print(listeners_id)
    #r.lpush(name,0)
    #r.flushall()


    #print(r.hget("meas:info:id", "2"))
    #s=r.hgetall(name)
    #print(os.path.dirname(__file__))
    #print(r.lrange(name,0,-1))
    print(r.keys())


if __name__ == "__main__":
    main()

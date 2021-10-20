from redis.client import Redis
import xlwings as xw
import redis
from dotenv import dotenv_values
import json
import os

from tkinter import Tk
from tkinter import messagebox

window = Tk()
window.withdraw()# Спрятать окно

def main():

    env_path = os.path.join(os.path.dirname(__file__),".env")
    config = dotenv_values(env_path)
    
    try :
        r = redis.Redis(host=config['HOST'], port=6379, db=0)
        r.ping()
    except :
        messagebox.showerror(
            title="Ошибка",
            message="""
            Нет доступа к серверу приложения.
            Обратитесь к системному администратору.
            """
        )
        return

    wb = xw.Book.caller()
    sheet = wb.sheets[0]
    
    row_num = wb.selection.row
    
    meas_list = []
    num_measurment = 0
    
    meas_val = lambda x,y : sheet.range(x,y+3).value
    
    while meas_val(2,num_measurment):
        meas_list.append(
            (
            #Номинальное значение 
            meas_val(2,num_measurment),
            #Верхний допуск 
            meas_val(3,num_measurment),
            #Нижний допуск 
            meas_val(4,num_measurment),
            #Измеренный размер
            meas_val(row_num,num_measurment)
            )
        )
        num_measurment+=1


    r_event_name =  "QC:event"  
    r_meas_list = "QC:meas:list" 
    r_id = 'QC:meas:id'

    head = [
        os.path.splitext(wb.name)[0] ,
        int(meas_val(row_num,1-3)),
        int(meas_val(row_num,2-3)) 
    ] 

    r_data = {
        "head" : head,
        "body" : meas_list
    }

    id = 1
    if not r.exists(r_id) :
        r.set(r_id, id)
    else:
        id = r.incr(r_id)

    r_data["head"].append(id)
    
    r_user_set = 'listener:set'
    users = r.smembers(r_user_set)

    listeners_str = ""
    for user in users:
        user = user.decode('utf-8')
        user = int(user)
        r_user = f'listener:{user}'
        if r.exists(r_user):
            user_context = json.loads( r.get(r_user) )
            listeners_str += user_context['name'] + '\n'

    if listeners_str == "":
        messagebox.showerror(
            title="Ошибка",
            message="""
            Внимание!
            Никто не подключен к уведомлениям.
            Сообщение не будет отправлено.
            """
        )
        return
    messagebox.showinfo(
        title="Уведомление",
        message=
            f"Партия: \t\t{head[0]}\n"
            f"Номер коробки: \t{head[1]}\n"
            f"Номер детали: \t{head[2]}\n"
            f"id:\t\t{id}\n"
            "Получатели : " +
            listeners_str
    )

    #Добавит запись в список, если записей больше 10, удалит первую
    max_len_list = 10
    if r.rpush(r_meas_list, json.dumps(r_data)) > max_len_list:
        r.lpop(r_meas_list) 


    r.set(r_event_name,1)
    


@xw.func
def hello(name):
    return f"Hello {name}!"


if __name__ == "__main__":
    xw.Book("myproject.xlsm").set_mock_caller()
    main()

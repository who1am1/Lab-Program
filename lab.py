from tkinter import *
from tkinter import messagebox
import string
import random
import sqlite3
import time

# хранит информацию, видно сейчас пароль или нет
visible_password = False

# имя вошедшего пользователя
username = ''

# считаем сколько раз пользователь ввел неправильно логин, пароль или капчу
failed_login = 0

# отмечаем количество секунд, которое было "на часах", когда пользователь неправильно ввел капчу
seconds = 0

# сколько секунд длится блокировка входа
block_seconds = 10

try:
    con = sqlite3.connect('lab.db')
    c = con.cursor()
    c.execute('''create table if not exists users(
                    login text not null primary key,
                    password text not null,
                    surname text not null,
                    uname text not null,
                    patronymic text,
                    urole text not null,
                    last_date text not null,
                    last_time text not null);      
        ''')
    con.commit()
    con.close()

except Exception as ep:
    messagebox.showerror('', ep)


class MainMenu(Tk):
    def __init__(self):
        super().__init__()

        self.title('Главное меню')
        self.geometry('500x400')

        frame = Frame(self, padx=20, pady=20)
        frame.pack()
        con = sqlite3.connect('lab.db')
        c = con.cursor()
        c.execute(f"SELECT * FROM 'users' where login ='{username}'")
        result = c.fetchone()
        con.close()
        lsurname = Label(frame, text=result[2], font=("Times", "10"))
        lsurname.grid(row=1, column=1)
        lname = Label(frame, text=result[3], font=("Times", "10"))
        lname.grid(row=1, column=2)
        lrole = Label(frame, text=result[5], font=("Times", "10"))
        lrole.grid(row=1, column=3, padx=10)
        ltime = Label(frame, text='Время', font=("Times", "10"))
        ltime.grid(row=1, column=4, padx=10)
        bbiomaterial = Button(
            frame,
            text='Прием биоматериала',
            padx=20,
            pady=10,
            font=("Times", "14"),
            command=open_biomaterial
        )
        bbiomaterial.grid(row=2, column=3, pady=30)


class BiomaterialWindow(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title('Прием биоматериала')
        self.geometry('500x400')


def show_hide_password():
    global visible_password
    if visible_password:
        visible_password = False
        epassword.config(show='*')
        bshowpassword.config(text='Показать пароль')
    else:
        visible_password = True
        epassword.config(show='')
        bshowpassword.config(text='Скрыть пароль')


def create_captcha():
    global captcha_text
    ecaptcha.delete(0, END)
    captcha.delete('all')
    captcha.grid()
    ecaptcha.grid()
    bupdate_captcha.grid()
    captcha_text = ''
    x_min = 40
    x_max = 55
    y_min = 30
    y_max = 40
    for _ in range(4):
        letter = random.choice(string.ascii_uppercase + '0123456789')
        captcha_text += letter
        captcha.create_text(random.randint(x_min, x_max), random.randint(y_min, y_max), text=letter, font='Times 24')
        x_min += 11
        x_max += 11
        y_min += 7
        y_max += 7


def open_mainmenu():
    global main_menu
    auth.withdraw()
    main_menu = MainMenu()


def open_biomaterial():
    global biomaterial
    biomaterial = BiomaterialWindow(main_menu)
    biomaterial.grab_set()


def sign_in():
    global failed_login
    global captcha_text
    global seconds
    global username
    warn = ''
    if (time.perf_counter() - seconds) < block_seconds:
        warn = 'Блокировка входа!'
    elif elogin.get() == '':
        warn = 'Введите логин!'
    elif epassword.get() == '':
        warn = 'Введите пароль!'
    elif (failed_login > 0) and (ecaptcha.get() != captcha_text):
        warn = f'Неправильный ввод капчи! Блокировка входа на {block_seconds} секунд'
        seconds = time.perf_counter()
        create_captcha()

    if warn != '':
        messagebox.showerror('Ошибка', warn)
    else:
        con = sqlite3.connect('lab.db')
        c = con.cursor()
        c.execute("SELECT password FROM 'users' where login =" + f"'{elogin.get()}'")
        result = c.fetchone()
        con.close()
        if result is None:
            messagebox.showerror('Ошибка', 'Неправильный логин или пароль!')
            create_captcha()
            failed_login += 1
        elif result[0] != epassword.get():
            messagebox.showerror('Ошибка', 'Неправильный логин или пароль!')
            create_captcha()
            failed_login += 1
        else:
            failed_login = 0
            username = elogin.get()
            open_mainmenu()
            captcha.update()
            captcha.postscript(file='file_name.ps')


auth = Tk()
auth.title("Лаборатория")
auth.geometry('500x400')

frame = Frame(auth, padx=20, pady=20)
frame.pack(expand=True)

Label(
    frame,
    text="Логин",
    font=("Times", "14")
).grid(row=1, column=1, pady=10)

Label(
    frame,
    text="Пароль",
    font=("Times", "14")
).grid(row=2, column=1, pady=5)

bshowpassword = Button(
    frame,
    text='Показать пароль',
    font=("Times", "8", 'underline'),
    command=show_hide_password
)
bshowpassword.grid(row=2, column=3)

elogin = Entry(frame, width=20)
epassword = Entry(frame, width=20, show='*')
elogin.grid(row=1, column=2)
epassword.grid(row=2, column=2)

bsign_in = Button(
    frame,
    text='Войти',
    padx=20,
    pady=10,
    font=("Times", "14"),
    command=sign_in
)
bsign_in.grid(row=4, column=2, pady=10)

captcha = Canvas(
    frame,
    width=150,
    height=100
)
captcha.grid(row=3, column=1)

ecaptcha = Entry(frame, width=20)
ecaptcha.grid(row=3, column=2)

bupdate_captcha = Button(
    frame,
    text='Обновить captcha',
    font=("Times", "8", 'underline'),
    command=create_captcha
)
bupdate_captcha.grid(row=3, column=3)

captcha_text = ''

captcha.grid_remove()
ecaptcha.grid_remove()
bupdate_captcha.grid_remove()

auth.mainloop()

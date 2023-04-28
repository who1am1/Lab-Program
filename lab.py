from tkinter import *
from tkinter import messagebox
import string
import random
import sqlite3
import time
import re

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
                    last_time text not null
                    );      
        ''')
    con.commit()

    c.execute('''create table if not exists insurance_type(
                    id integer not null primary key,
                    uname text not null
                    );      
        ''')
    con.commit()

    c.execute('''create table if not exists insurance_company(
                    id integer not null primary key,
                    uname text not null,
                    address text not null,
                    inn text not null,
                    rs text not null,
                    bik text not null
                    );      
        ''')
    con.commit()

    c.execute('''create table if not exists patients(
                    id integer not null primary key,
                    surname text not null,
                    uname text not null,
                    patronymic text,
                    birthdate text not null,
                    passport text not null,
                    telephone text not null,
                    email text,
                    insurance_number text not null,
                    insurance_type text not null,
                    insurance_company text not null,
                    FOREIGN KEY(insurance_type) REFERENCES insurance_type(id),
                    FOREIGN KEY(insurance_company) REFERENCES insurance_company(id)
                    );      
        ''')
    con.commit()

    c.execute('''create table if not exists services(
                    id integer not null primary key,
                    uname text not null,
                    price integer not null,
                    lead_time text not null,
                    mean_deviation text 
                    );      
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
        frame = Frame(self, padx=20, pady=20)
        frame.pack()

        Label(
            frame,
            text="Код пробирки",
            font=("Times", "14")
        ).grid(row=1, column=1)

        self.ecode = Entry(frame, width=20)
        self.ecode.grid(row=1, column=2, padx=15)

        bbarcode = Button(
            frame,
            text='Сгенерировать штрихкод',
            font=("Times", "10"),
            command=self.generate_barcode
        )
        bbarcode.grid(row=2, column=1, pady=10)

        self.barcode = Canvas(
            frame,
            width=300,
            height=129.65
        )
        self.barcode.grid(row=2, column=2, pady=15)

        Label(
            frame,
            text="Пациент",
            font=("Times", "14")
        ).grid(row=3, column=1)

        patient_text = StringVar()
        patient = Entry(
            frame,
            textvariable=patient_text,
            state='readonly',
            width=30
        )
        patient.grid(row=3, column=2)

        Button(
            frame,
            text='...',
            font=("Times", "10"),
            command=open_patient
        ).grid(row=3, column=3)

    def generate_barcode(self):
        if len(self.ecode.get()) != 13:
            messagebox.showerror('Ошибка', 'Неправильный код!')
            return
        # Расчет контрольной (тринадццатой) цифры:
        code = self.ecode.get()
        even = 0
        odd = 0
        for i in range(12):
            # odd и even поменяны местами в конструкции if-else, т.к. список идет с 0
            if i % 2 == 0:
                odd += int(code[i])
            else:
                even += int(code[i])
        res = even * 3 + odd
        if res % 10 == 0:
            res = 0
        else:
            res = (res // 10 + 1) * 10 - res

        if int(code[12]) != res:
            messagebox.showerror('Ошибка', f'Неправильная контрольная последняя цифра! Попробуйте цифру {res}')
            return

        # первая цифра в штриходе указывает, по какому шаблону должны идти следующие шесть цифр
        # другие шесть цифр идут всегда по шаблону 'RRRRRR'
        barcode_pattern = [
            'LLLLLLRRRRRR',  # шаблон для первой цифры 0
            'LLGLGGRRRRRR',  # шаблон для первой цифры 1
            'LLGGLGRRRRRR',
            'LLGGGLRRRRRR',
            'LGLLGGRRRRRR',
            'LGGLLGRRRRRR',
            'LGGGLLRRRRRR',
            'LGLGLGRRRRRR',
            'LGLGGLRRRRRR',
            'LGGLGLRRRRRR'  # шаблон для первой цифры 9
        ]

        # R-коды цифр
        r_code = [
            '3b 2w 1b 1w',  # для цифры 0
            '2b 2w 2b 1w',  # для цифры 1
            '2b 1w 2b 2w',
            '1b 4w 1b 1w',
            '1b 1w 3b 2w',
            '1b 2w 3b 1w',
            '1b 1w 1b 4w',
            '1b 3w 1b 2w',
            '1b 2w 1b 3w',
            '3b 1w 1b 2w'  # для цифры 9
        ]
        """
        L-код отличается от R-кода фотографически негативным исполнением
        (там, где был черный, будет белый и наоборот)
        Пример:
        R-code цифры 0: 3b 2w 1b 1w
        L-code цифры 0: 3w 2b 1w 1b
        
        G-код отличается от R-кода зеркальным исполнением
        (переворачиваем строку)
        Пример:
        R-code цифры 0: 3b 2w 1b 1w
        G-code цифры 0: 1w 1b 2w 3b
        """

        shtrih_height = 22.85
        shtrih_height_add = 1.65
        digit_height = 2.75
        space_between_digit_n_shtrih = 0.165
        k_shtrih_width = 0.5
        zero_shtrih_width = 1.35
        space_between_shtrih = 0.2
        free_zone_left = 3.63
        free_zone_right = 2.31

        k_scale = 5
        shtrih_x = free_zone_right

        self.barcode.delete('all')

        current_pattern = ''
        i = 1

        for digit in code:
            if i == 1:
                # Рисуем первый разделяющий знак: 1 черная полоска, 1 белая, 1 черная. Длина каждой - единичная
                current_pattern = barcode_pattern[int(digit)]
                self.barcode.create_rectangle(shtrih_x * k_scale, 0, (shtrih_x + k_shtrih_width * 1) * k_scale,
                                              (shtrih_height + shtrih_height_add) * k_scale, fill='black')
                shtrih_x = (shtrih_x + k_shtrih_width * 1) * k_scale
                shtrih_x += k_shtrih_width * k_scale
                self.barcode.create_rectangle(shtrih_x, 0, shtrih_x + k_shtrih_width * 1 * k_scale,
                                              (shtrih_height + shtrih_height_add) * k_scale, fill='black')
                shtrih_x += k_shtrih_width * k_scale

                self.barcode.create_text(shtrih_x - (k_shtrih_width * 5.5) * k_scale,
                                         (shtrih_height + space_between_digit_n_shtrih + 2) * k_scale, text=digit,
                                         font=f'Times {3 * k_scale}')

                i += 1
                continue

            # Определем, какой шаблон используется
            shtrih_pattern = r_code[int(digit)].split(sep=' ')
            if current_pattern[i - 2] == 'L':
                for j in range(4):
                    if 'b' in shtrih_pattern[j]:
                        shtrih_pattern[j] = shtrih_pattern[j].replace('b', 'w')
                        continue
                    if 'w' in shtrih_pattern[j]:
                        shtrih_pattern[j] = shtrih_pattern[j].replace('w', 'b')
            elif current_pattern[i - 2] == 'G':
                shtrih_pattern.reverse()

            # Рисуем разделяющий серединный знак: 1 белая полоска, 1 черная, 1 белая, 1 черная, 1 белая. Длина каждой - единичная
            if i == 8:
                shtrih_x += k_shtrih_width * k_scale
                self.barcode.create_rectangle(shtrih_x, 0, shtrih_x + k_shtrih_width * 1 * k_scale,
                                              (shtrih_height + shtrih_height_add) * k_scale, fill='black')
                shtrih_x += k_shtrih_width * k_scale
                shtrih_x += k_shtrih_width * k_scale
                self.barcode.create_rectangle(shtrih_x, 0, shtrih_x + k_shtrih_width * 1 * k_scale,
                                              (shtrih_height + shtrih_height_add) * k_scale, fill='black')
                shtrih_x += k_shtrih_width * k_scale
                shtrih_x += k_shtrih_width * k_scale

            # Рисуем каждый штрих. Одна цифра отобржается 2 белыми полосками и 2 черными.
            for shtrih in shtrih_pattern:
                if 'w' in shtrih:
                    shtrih_x += k_shtrih_width * int(shtrih[0]) * k_scale
                    continue
                self.barcode.create_rectangle(shtrih_x, 0, shtrih_x + k_shtrih_width * int(shtrih[0]) * k_scale,
                                              shtrih_height * k_scale, fill='black')
                shtrih_x += k_shtrih_width * int(shtrih[0]) * k_scale

            self.barcode.create_text(shtrih_x - (k_shtrih_width * int(shtrih_pattern[3][0]) + 1) * k_scale,
                                     (shtrih_height + space_between_digit_n_shtrih + 2) * k_scale, text=digit,
                                     font=f'Times {3 * k_scale}')

            # Рисуем последний разделяющий знак: 1 черная полоска, 1 белая, 1 черная. Длина каждой - единичная
            if i == 13:
                self.barcode.create_rectangle(shtrih_x, 0, shtrih_x + k_shtrih_width * 1 * k_scale,
                                              (shtrih_height + shtrih_height_add) * k_scale, fill='black')
                shtrih_x += k_shtrih_width * k_scale
                shtrih_x += k_shtrih_width * k_scale
                self.barcode.create_rectangle(shtrih_x, 0, shtrih_x + k_shtrih_width * 1 * k_scale,
                                              (shtrih_height + shtrih_height_add) * k_scale, fill='black')

            i += 1

class PatientWindow(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title('Выберите пациента')
        self.geometry('500x400')
        frame = Frame(self, padx=20, pady=20)
        frame.pack()

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

def open_patient():
    global patient_info
    patient_info = PatientWindow(biomaterial)
    patient_info.grab_set()

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

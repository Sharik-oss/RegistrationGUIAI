import os
from tkinter import *
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo, showerror
from PIL import Image, ImageTk
from cryptography.fernet import Fernet
import sqlite3
import cv2
import numpy as np
from registration import FaceRecognition


def convert_to_binary_data(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        blob_data = file.read()
    return blob_data


def write_to_file(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)


def mse(img1, img2):
    diff = cv2.subtract(img1, img2)
    err = np.sum(diff ** 2)
    return diff


def read_blob_data(email):
    try:
        sqlite_connection = sqlite3.connect('Users.db')
        cursor = sqlite_connection.cursor()
        print("Connected to SQLite")

        sql_fetch_blob_query = """SELECT Image from Users where Email = ?"""
        cursor.execute(sql_fetch_blob_query, (email,))
        record = cursor.fetchall()
        print("Storing employee image and resume on disk \n")
        for row in record:
            photo = row[0]

            print("Storing employee image and resume on disk \n")

            photo_path = fr"faces\{email}.jpg"
            write_to_file(photo, photo_path)

        cursor.close()

        fr = FaceRecognition()
        fr.run_recognition()
        os.remove(f"faces/{email}.jpg")

    except sqlite3.Error as error:
        print("Failed to read blob data from sqlite table", error)
    finally:
        print("sqlite connection is closed")


def capture(image):
    face_detection = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
    vid = cv2.VideoCapture(0)
    data = image.fetchone()[0]
    img2 = np.frombuffer(data, np.uint8)
    while True:
        ret, frame = vid.read()
        dim = (607, 607)
        img2.resize(dim)
        face = face_detection.detectMultiScale(frame, 1.1, 5)
        for (x, y, w, h) in face:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow('Frame', frame)
        frame_shape = frame.shape[:2]
        mse = np.mean((img2 - frame_shape) ** 2)
        psnr = 10 * np.log10((255 ** 2) / mse)
        if psnr > 30:
            showinfo("Info", "These photoes are the same")
            break
        else:
            showinfo("Info", "These photoes are not the same, please do something")
            break

    vid.release()
    cv2.destroyAllWindows()


def registration():
    def fileopen():
        global picture_path
        file_types = (
            ("Photo files", ".jpg .jpeg .png"),
            ("All files", "*.*")
        )
        picture_path = fd.askopenfilename(
            title="Select file",
            initialdir="C:/",
            filetypes=file_types
        )
        if picture_path:
            image = Image.open(picture_path)
            image = image.resize((200,200))
            photo = ImageTk.PhotoImage(image)
            picture_label.config(image=photo)
            picture_label.image = photo

    def register_db():
        try:
            if password.get() == repeat_password.get():
                sqlite_connection = sqlite3.connect("Users.db")
                cursor = sqlite_connection.cursor()
                print("Connected to the db:)")
                user_name = name_entry.get()
                second_name_val = second_name.get()
                image = picture_path
                converted_image = convert_to_binary_data(image)
                email_value = email.get()
                password_val = password.get()
                encrypt_password = password_val.encode()
                key = Fernet.generate_key()
                f = Fernet(key)
                encrypted_password = f.encrypt(encrypt_password)
                print(converted_image)

                sqlite_insert = f'''
                            INSERT INTO Users(name, "Second name", Email, Password, Image)
                            VALUES(?, ?, ?, ?, ?)
    '''
                data_tuple = (user_name, second_name_val, email_value, encrypted_password, converted_image)
                cursor.execute(sqlite_insert, data_tuple)

                sqlite_show = '''
                    SELECT * FROM Users
                '''

                print(cursor.execute(sqlite_show).fetchall())
                print("record inserted")
                sqlite_connection.commit()
                cursor.close()
                reg_window.withdraw()
                root.deiconify()
            else:
                showinfo("Error", "პაროლები არ ემთხვევა ერთმანეთს...")

        except sqlite3.Error as error:
            print(error)
        finally:
            if sqlite_connection:
                sqlite_connection.close()
                print("Connection was closed")

    root.withdraw()
    reg_window = Toplevel()
    reg_window.resizable(False, False)
    reg_window.title("რეგისტრაცია")
    reg_window.geometry("400x500")
    name_label = Label(reg_window, text="სახელი:")
    name_label.pack()
    name_entry = Entry(reg_window)
    name_entry.pack()
    second_name_label = Label(reg_window, text="გვარი:")
    second_name_label.pack()
    second_name = Entry(reg_window)
    second_name.pack()
    email_label = Label(reg_window, text="ელ.ფოსტა:")
    email_label.pack()
    email = Entry(reg_window)
    email.pack()
    phone_number_label = Label(reg_window, text="ტელეფონის ნომერი:")
    phone_number_label.pack()
    phone_number = Entry(reg_window)
    phone_number.pack()
    password_label = Label(reg_window, text="პაროლი:")
    password_label.pack()
    password = Entry(reg_window, show="*")
    password.pack()
    repeat_password_label = Label(reg_window, text="გაიმეორე პაროლი:")
    repeat_password_label.pack()
    repeat_password = Entry(reg_window, show="*")
    repeat_password.pack()
    picture_button = Button(reg_window, text="აირჩიე ფოტო", command=fileopen)
    picture_button.pack()
    picture_label = Label(reg_window)
    picture_label.pack()

    register_button = Button(reg_window, text="რეგისტრაცია", command=register_db)
    register_button.pack()


def login():
    user_name = user_name_entry.get()
    password = user_password.get()
    # print(str(user_name) + " " + str(password))
    sqlite_connection = sqlite3.connect("Users.db")
    cursor = sqlite_connection.cursor()
    sql_get_user_pass = f'''
            SELECT Password, Image FROM Users WHERE Email = "{str(user_name)}"
    '''
    cursor.execute(sql_get_user_pass)
    sql_get_user_image = f'''
                SELECT Image FROM Users WHERE Email = "{str(user_name)}"
        '''
    image = cursor.execute(sql_get_user_image)

    if cursor.fetchone() is not None:
        showinfo("Info", "პაროლი სწორია")
        read_blob_data(user_name)
    else:
        showerror('Error', "პაროლი არასწორია")


root = Tk()
root.geometry("400x500")
root.title("Registration")
root.resizable(False, False)
user_name_label = Label(root, text="ელ.ფოსტა: ")
user_name_label.pack()
user_name_entry = Entry(root)
user_name_entry.pack()
user_password_label = Label(root, text="პაროლი: ")
user_password_label.pack()
user_password = Entry(root, show="*")
user_password.pack()
login_button = Button(root, text="შესვლა", command=login)
login_button.pack()
no_acc_button = Button(root, text="არ გაქვს ანგარიში?", command=registration)
no_acc_button.pack()
root.mainloop()

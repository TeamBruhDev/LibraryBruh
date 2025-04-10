from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    Модель пользователя системы.

    Атрибуты:
        id (int): Уникальный идентификатор пользователя.
        username (str): Имя пользователя (логин), должно быть уникальным.
        password (str): Хэшированный пароль пользователя.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Book(db.Model):
    """
    Модель книги, загруженной пользователем.

    Атрибуты:
        id (int): Уникальный идентификатор книги.
        title (str): Название книги (или имя файла).
        path (str): Путь к файлу книги на сервере.
        user_id (int): ID пользователя, загрузившего книгу (внешний ключ).
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    path = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Bookmark(db.Model):
    """
    Модель закладки, содержащая позицию чтения пользователя в конкретной книге.

    Атрибуты:
        id (int): Уникальный идентификатор закладки.
        user_id (int): ID пользователя, сделавшего закладку.
        book_id (int): ID книги, к которой относится закладка.
        position (int): Позиция в тексте книги, на которой пользователь остановился.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    position = db.Column(db.Integer, default=0)


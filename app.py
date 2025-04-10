from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import *
from forms import LoginForm, RegisterForm
import os
from lxml import etree

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def parse_fb2_text(path):
    """Парсит и возвращает текст из FB2-файла по указанному пути."""
    try:
        tree = etree.parse(path)
        body = tree.find('.//body')
        paragraphs = body.findall('.//p')
        return '\n\n'.join([p.text for p in paragraphs if p.text])
    except Exception as e:
        return f"Ошибка при чтении FB2: {str(e)}"


@login_manager.user_loader
def load_user(user_id):
    """Загружает пользователя по ID для Flask-Login."""
    return User.query.get(int(user_id))


@app.before_request
def create_tables():
    """Создаёт таблицы в базе данных при первом запуске приложения."""
    db.create_all()


@app.route('/')
def index():
    """Главная страница сервиса."""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя."""
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Авторизация пользователя."""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('library'))
        flash('Неверный логин или пароль')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """Выход из аккаунта."""
    logout_user()
    return redirect(url_for('index'))


@app.route('/library')
@login_required
def library():
    """Просмотр библиотеки пользователя."""
    books = Book.query.filter_by(user_id=current_user.id).all()
    return render_template('library.html', books=books)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Загрузка новой книги в формате FB2."""
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.fb2'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            new_book = Book(title=file.filename, user_id=current_user.id, path=filepath)
            db.session.add(new_book)
            db.session.commit()
            return redirect(url_for('library'))
    return render_template('upload.html')


@app.route('/read/<int:book_id>')
@login_required
def read(book_id):
    """Отображение текста книги FB2 с поддержкой чтения и пагинации."""
    book = Book.query.get_or_404(book_id)
    if book.user_id != current_user.id:
        return "Доступ запрещён", 403

    if not book.path.endswith('.fb2'):
        return "Чтение поддерживается только для FB2", 400

    content = parse_fb2_text(book.path)
    if not content:
        return "Ошибка чтения книги"

    # Поддержка закладок
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, book_id=book.id).first()
    position = bookmark.position if bookmark else 0

    # Ограничим длину страницы (например, 2000 символов)
    PAGE_SIZE = 2000
    page = content[position:position + PAGE_SIZE]
    next_pos = position + PAGE_SIZE if position + PAGE_SIZE < len(content) else None

    return render_template('read.html', title=book.title, page=page, book_id=book.id, next_pos=next_pos)


@app.route('/bookmark/<int:book_id>/<int:position>')
@login_required
def bookmark(book_id, position):
    """Сохраняет позицию чтения (закладку) для указанной книги."""
    bookmark = Bookmark.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if not bookmark:
        bookmark = Bookmark(user_id=current_user.id, book_id=book_id, position=position)
        db.session.add(bookmark)
    else:
        bookmark.position = position
    db.session.commit()
    return redirect(url_for('read', book_id=book_id))

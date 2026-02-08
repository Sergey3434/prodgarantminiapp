from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
import requests
import shutil
import uuid
import random
import string

app = Flask(__name__)
CORS(app)

# Конфигурация
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///real_estate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Конфигурация Telegram бота
app.config['TELEGRAM_BOT_TOKEN'] = '8322515217:AAERPx1g-9_bIkS-iC30UoVsNiZT4b_rC9I'
app.config['TELEGRAM_CHAT_ID'] = '793965845'

# Создаем папку для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)


# Модели базы данных
class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.String(100), nullable=False)
    market = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    jk = db.Column(db.String(100))
    address = db.Column(db.String(200), nullable=False)
    district = db.Column(db.String(100))
    description = db.Column(db.Text, nullable=False)
    images = db.Column(db.Text, nullable=False)
    is_hot = db.Column(db.Boolean, default=False)
    is_hit = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


class Banner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200))
    link = db.Column(db.String(200))
    page = db.Column(db.String(50), nullable=False, default='home')
    target_property_id = db.Column(db.Integer)
    target_jk = db.Column(db.String(100))
    market = db.Column(db.String(50))
    type = db.Column(db.String(50))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(100), unique=True, nullable=False)
    items = db.Column(db.Text, nullable=False)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(50))
    customer_tg_id = db.Column(db.String(100))
    status = db.Column(db.String(50), default='Новый')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SellRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    photos = db.Column(db.Text)
    status = db.Column(db.String(50), default='Новая')
    is_active = db.Column(db.Boolean, default=True)
    customer_tg_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    tg_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Функция для полного обновления базы данных
def reset_database():
    """Полностью пересоздает базу данных"""
    db_path = 'real_estate.db'

    if os.path.exists(db_path):
        print("🔄 Удаление старой базы данных...")
        try:
            # Создаем резервную копию
            backup_path = f'real_estate_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
            shutil.copy2(db_path, backup_path)
            print(f"✅ Резервная копия создана: {backup_path}")

            # Удаляем старую базу
            os.remove(db_path)
            print("🗑️ Старая база удалена")
        except Exception as e:
            print(f"❌ Ошибка при удалении базы: {e}")
            return False

    # Создаем новую базу
    print("🆕 Создание новой базы данных...")
    try:
        db.create_all()
        print("✅ Новая база данных создана с обновленной структурой")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании базы: {e}")
        return False


# Создаём базу при запуске
with app.app_context():
    reset_database()


def generate_unique_number():
    """Генерирует уникальный номер с буквами, цифрами и спецсимволами"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits + '!@#$', k=8))
    return f"{timestamp}-{random_chars}"


def generate_property_number():
    """Генерирует уникальный номер объявления"""
    return generate_unique_number()


def generate_order_number():
    """Генерирует уникальный номер заказа"""
    return generate_unique_number()


def generate_request_number():
    """Генерирует уникальный номер заявки"""
    return generate_unique_number()


def save_file(file):
    """Сохраняет файл и возвращает путь"""
    if file:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f'/uploads/{filename}'
    return None


def get_full_url(path):
    """Возвращает полный URL для файла"""
    return f"{request.host_url.rstrip('/')}{path}"


def send_telegram_message(text):
    """
    Отправляет сообщение в Telegram
    """
    bot_token = app.config['TELEGRAM_BOT_TOKEN']
    chat_id = app.config['TELEGRAM_CHAT_ID']

    if not bot_token or not chat_id:
        print("⚠️ Telegram бот не настроен. Сообщение не отправлено.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Экранируем специальные символы для Markdown
    text = text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')

    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': True
    }

    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ Сообщение отправлено в Telegram")
            return True
        else:
            print(f"❌ Ошибка отправки сообщения: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Исключение при отправке сообщения: {e}")
        return False


def format_order_message(order):
    items = json.loads(order.items)
    items_text = "\n".join([
        f"• *{item.get('title', 'Объект')}*\n"
        f"  Адрес: {item.get('address', '-')}\n"
        f"  Цена: {item.get('price', '-')}"
        for item in items
    ])
    message = (
        f"🔔 *НОВЫЙ ЗАКАЗ* #{order.order_number}\n\n"
        f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"*Список объектов:*\n{items_text}\n\n"
        f"*Контактные данные:*\n"
        f"👤 Имя: {order.customer_name or '—'}\n"
        f"📱 Телефон: {order.customer_phone or '—'}\n"
        f"🆔 Telegram ID: {order.customer_tg_id or '—'}\n\n"
        f"📊 Статус: {order.status}"
    )
    return message


def format_sell_request_message(sell_request):
    emoji = "🛒" if sell_request.type == "buy" else "💰"
    request_type = "ПОКУПКА" if sell_request.type == "buy" else "ПРОДАЖА"
    photos_text = ""
    if sell_request.photos:
        photos = json.loads(sell_request.photos)
        if photos:
            photos_text = f"\n📷 *Фотографии:* {len(photos)} шт."
    message = (
        f"{emoji} *НОВАЯ ЗАЯВКА* #{sell_request.request_number}\n\n"
        f"📅 Дата: {sell_request.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"*Тип заявки:* {request_type}\n\n"
        f"*Контактные данные:*\n"
        f"👤 Имя: {sell_request.name}\n"
        f"📱 Телефон: {sell_request.phone}\n\n"
        f"*Адрес/Район:*\n"
        f"{sell_request.address}\n\n"
        f"*Описание:*\n"
        f"{sell_request.description}{photos_text}\n\n"
        f"📊 Статус: {sell_request.status}"
    )
    return message


# === API ЭНДПОИНТЫ ===

@app.route('/api/properties', methods=['GET'])
def get_properties():
    market = request.args.get('market')
    type_ = request.args.get('type')
    jk = request.args.get('jk')
    search = request.args.get('search')
    districts = request.args.getlist('districts')

    query = Property.query.filter_by(is_active=True)
    if market and market != 'all': query = query.filter_by(market=market)
    if type_: query = query.filter_by(type=type_)
    if jk: query = query.filter_by(jk=jk)
    if districts: query = query.filter(Property.district.in_(districts))
    if search:
        search = f"%{search}%"
        query = query.filter(db.or_(
            Property.title.like(search),
            Property.address.like(search),
            Property.description.like(search),
            Property.jk.like(search) if Property.jk else False,
            Property.district.like(search) if Property.district else False,
            Property.property_number.like(search)
        ))

    properties = query.all()
    result = [{
        'id': p.id,
        'property_number': p.property_number,
        'title': p.title,
        'price': p.price,
        'market': p.market,
        'type': p.type,
        'jk': p.jk,
        'address': p.address,
        'district': p.district,
        'description': p.description,
        'images': json.loads(p.images),
        'is_hot': p.is_hot,
        'is_hit': p.is_hit,
        'created_at': p.created_at.isoformat()
    } for p in properties]
    return jsonify(result)


@app.route('/api/properties/hot', methods=['GET'])
def get_hot_properties():
    properties = Property.query.filter_by(is_active=True, is_hot=True).limit(2).all()
    result = [{
        'id': p.id,
        'property_number': p.property_number,
        'title': p.title,
        'price': p.price,
        'market': p.market,
        'type': p.type,
        'jk': p.jk,
        'address': p.address,
        'district': p.district,
        'description': p.description,
        'images': json.loads(p.images),
        'is_hot': p.is_hot,
        'is_hit': p.is_hit
    } for p in properties]
    return jsonify(result)


@app.route('/api/properties/hit', methods=['GET'])
def get_hit_properties():
    properties = Property.query.filter_by(is_active=True, is_hit=True).limit(2).all()
    result = [{
        'id': p.id,
        'property_number': p.property_number,
        'title': p.title,
        'price': p.price,
        'market': p.market,
        'type': p.type,
        'jk': p.jk,
        'address': p.address,
        'district': p.district,
        'description': p.description,
        'images': json.loads(p.images),
        'is_hot': p.is_hot,
        'is_hit': p.is_hit
    } for p in properties]
    return jsonify(result)


@app.route('/api/properties/<int:property_id>', methods=['GET'])
def get_property(property_id):
    prop = Property.query.get_or_404(property_id)
    if not prop.is_active:
        return jsonify({'error': 'Объявление не активно'}), 404
    return jsonify({
        'id': prop.id,
        'property_number': prop.property_number,
        'title': prop.title,
        'price': prop.price,
        'market': prop.market,
        'type': prop.type,
        'jk': prop.jk,
        'address': prop.address,
        'district': prop.district,
        'description': prop.description,
        'images': json.loads(prop.images),
        'is_hot': prop.is_hot,
        'is_hit': prop.is_hit,
        'created_at': prop.created_at.isoformat()
    })


@app.route('/api/banners/home', methods=['GET'])
def get_home_banners():
    banners = Banner.query.filter_by(page='home', is_active=True).order_by(Banner.order).all()
    result = [{
        'id': b.id,
        'image': get_full_url(b.image_path),
        'title': b.title,
        'link': b.link,
        'order': b.order
    } for b in banners]
    return jsonify(result)


@app.route('/api/banners/thailand', methods=['GET'])
def get_thailand_banners():
    banners = Banner.query.filter_by(page='thailand', is_active=True).order_by(Banner.order).all()
    result = [{
        'id': b.id,
        'image': get_full_url(b.image_path),
        'title': b.title,
        'target_property_id': b.target_property_id,
        'order': b.order
    } for b in banners]
    return jsonify(result)


@app.route('/api/banners/jk', methods=['GET'])
def get_jk_banners():
    market = request.args.get('market')
    type_ = request.args.get('type')
    if not market or not type_:
        return jsonify({'error': 'Необходимо указать рынок и тип'}), 400

    banners = Banner.query.filter_by(page='jk', market=market, type=type_, is_active=True).order_by(Banner.order).all()
    result = []
    for banner in banners:
        property_count = Property.query.filter_by(market=market, type=type_, jk=banner.target_jk,
                                                  is_active=True).count()
        result.append({
            'id': banner.id,
            'image': get_full_url(banner.image_path),
            'title': banner.title,
            'target_jk': banner.target_jk,
            'property_count': property_count,
            'order': banner.order
        })
    return jsonify(result)


@app.route('/api/thailand', methods=['GET'])
def get_thailand_properties():
    properties = Property.query.filter_by(market='thailand', is_active=True).all()
    result = [{
        'id': p.id,
        'property_number': p.property_number,
        'title': p.title,
        'price': p.price,
        'type': p.type,
        'address': p.address,
        'district': p.district,
        'description': p.description,
        'images': json.loads(p.images),
        'is_hot': p.is_hot,
        'is_hit': p.is_hit
    } for p in properties]
    return jsonify(result)


@app.route('/api/properties/jk', methods=['GET'])
def get_properties_by_jk():
    market = request.args.get('market')
    type_ = request.args.get('type')
    jk = request.args.get('jk')
    if not market or not type_ or not jk:
        return jsonify({'error': 'Необходимо указать рынок, тип и ЖК'}), 400

    properties = Property.query.filter_by(market=market, type=type_, jk=jk, is_active=True).all()
    result = [{
        'id': p.id,
        'property_number': p.property_number,
        'title': p.title,
        'price': p.price,
        'market': p.market,
        'type': p.type,
        'jk': p.jk,
        'address': p.address,
        'district': p.district,
        'description': p.description,
        'images': json.loads(p.images),
        'is_hot': p.is_hot,
        'is_hit': p.is_hit,
        'created_at': p.created_at.isoformat()
    } for p in properties]
    return jsonify(result)


@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({'error': 'Неверные данные'}), 400

    order_number = generate_order_number()
    order = Order(
        order_number=order_number,
        items=json.dumps(data['items']),
        customer_name=data.get('customer_name'),
        customer_phone=data.get('customer_phone'),
        customer_tg_id=data.get('customer_tg_id'),
        status='Новый',
        is_active=True
    )
    db.session.add(order)
    db.session.commit()
    send_telegram_message(format_order_message(order))
    return jsonify({'success': True, 'order_number': order_number, 'message': 'Заказ успешно создан'})


@app.route('/api/orders', methods=['GET'])
def get_orders():
    tg_id = request.args.get('tg_id')
    query = Order.query.filter_by(is_active=True)
    if tg_id:
        query = query.filter_by(customer_tg_id=tg_id)
    orders = query.order_by(Order.created_at.desc()).all()
    result = [{
        'id': o.id,
        'order_number': o.order_number,
        'items': json.loads(o.items),
        'customer_name': o.customer_name,
        'customer_phone': o.customer_phone,
        'customer_tg_id': o.customer_tg_id,
        'status': o.status,
        'created_at': o.created_at.isoformat()
    } for o in orders]
    return jsonify(result)


@app.route('/api/sell-requests', methods=['POST'])
def create_sell_request():
    data = request.form
    if not data or 'type' not in data or 'name' not in data or 'phone' not in data or 'address' not in data or 'description' not in data:
        return jsonify({'error': 'Неверные данные'}), 400

    request_number = generate_request_number()
    photos = []
    if 'photos' in request.files:
        files = request.files.getlist('photos')
        for file in files[:5]:
            path = save_file(file)
            if path:
                photos.append(get_full_url(path))

    sell_request = SellRequest(
        request_number=request_number,
        type=data['type'],
        name=data['name'],
        phone=data['phone'],
        address=data['address'],
        description=data['description'],
        photos=json.dumps(photos) if photos else None,
        status='Новая',
        is_active=True,
        customer_tg_id=data.get('tg_id')
    )
    db.session.add(sell_request)
    db.session.commit()
    send_telegram_message(format_sell_request_message(sell_request))
    return jsonify({'success': True, 'request_number': request_number, 'message': 'Заявка успешно создана'})


@app.route('/api/sell-requests', methods=['GET'])
def get_sell_requests():
    tg_id = request.args.get('tg_id')
    query = SellRequest.query.filter_by(is_active=True)
    if tg_id:
        query = query.filter_by(customer_tg_id=tg_id)
    requests = query.order_by(SellRequest.created_at.desc()).all()
    result = [{
        'id': r.id,
        'request_number': r.request_number,
        'type': r.type,
        'name': r.name,
        'phone': r.phone,
        'address': r.address,
        'description': r.description,
        'photos': json.loads(r.photos) if r.photos else [],
        'status': r.status,
        'created_at': r.created_at.isoformat()
    } for r in requests]
    return jsonify(result)


@app.route('/api/track-visit', methods=['POST'])
def track_visit():
    """Отслеживает посещение сайта"""
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    tg_id = request.form.get('tg_id') or request.args.get('tg_id')

    visit = Visit(
        ip_address=ip_address,
        user_agent=user_agent,
        tg_id=tg_id
    )
    db.session.add(visit)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/admin/visits/today', methods=['GET'])
def get_today_visits():
    """Возвращает количество уникальных посещений за сегодня"""
    today = date.today()
    # Считаем уникальные по IP за сегодня
    visits = Visit.query.filter(db.cast(Visit.created_at, db.Date) == today).all()
    # Для демо считаем все посещения (не уникальные)
    return jsonify({'count': len(visits)})


# === АДМИНКА ЭНДПОИНТЫ ===

@app.route('/api/admin/properties', methods=['GET'])
def admin_get_properties():
    search = request.args.get('search')
    query = Property.query.filter_by(is_active=True)
    if search:
        search = f"%{search}%"
        query = query.filter(db.or_(
            Property.property_number.like(search),
            Property.title.like(search),
            Property.address.like(search)
        ))
    properties = query.order_by(Property.created_at.desc()).all()
    result = [{
        'id': p.id,
        'property_number': p.property_number,
        'title': p.title,
        'price': p.price,
        'market': p.market,
        'type': p.type,
        'jk': p.jk,
        'address': p.address,
        'district': p.district,
        'description': p.description,
        'images': json.loads(p.images),
        'is_hot': p.is_hot,
        'is_hit': p.is_hit,
        'is_active': p.is_active,
        'created_at': p.created_at.isoformat()
    } for p in properties]
    return jsonify(result)


@app.route('/api/admin/properties', methods=['POST'])
def admin_create_property():
    data = request.form
    images = []
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files[:10]:
            path = save_file(file)
            if path:
                images.append(get_full_url(path))

    # Получаем уникальный шифр от админа или генерируем автоматически
    property_number = data.get('property_number', generate_property_number())

    # Проверяем уникальность шифра
    existing = Property.query.filter_by(property_number=property_number).first()
    if existing:
        return jsonify({'error': f'Шифр "{property_number}" уже существует. Выберите другой.'}), 400

    property_obj = Property(
        property_number=property_number,
        title=data['title'],
        price=data['price'],
        market=data['market'],
        type=data['type'],
        jk=data.get('jk'),
        address=data['address'],
        district=data.get('district'),
        description=data['description'],
        images=json.dumps(images),
        is_hot=data.get('is_hot') == 'on',
        is_hit=data.get('is_hit') == 'on',
        is_active=True
    )
    db.session.add(property_obj)
    db.session.commit()
    return jsonify(
        {'success': True, 'id': property_obj.id, 'property_number': property_number, 'message': 'Объявление создано'})


@app.route('/api/admin/properties/<int:property_id>', methods=['PUT'])
def admin_update_property(property_id):
    property_obj = Property.query.get_or_404(property_id)
    data = request.form
    property_obj.title = data.get('title', property_obj.title)
    property_obj.price = data.get('price', property_obj.price)
    property_obj.market = data.get('market', property_obj.market)
    property_obj.type = data.get('type', property_obj.type)
    property_obj.jk = data.get('jk', property_obj.jk)
    property_obj.address = data.get('address', property_obj.address)
    property_obj.district = data.get('district', property_obj.district)
    property_obj.description = data.get('description', property_obj.description)
    property_obj.is_hot = data.get('is_hot') == 'on'
    property_obj.is_hit = data.get('is_hit') == 'on'
    property_obj.property_number = data.get('property_number', property_obj.property_number)

    if 'images' in request.files:
        files = request.files.getlist('images')
        new_images = []
        for file in files[:10]:
            path = save_file(file)
            if path:
                new_images.append(get_full_url(path))
        if new_images:
            property_obj.images = json.dumps(new_images)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Объявление обновлено'})


@app.route('/api/admin/properties/<int:property_id>', methods=['DELETE'])
def admin_delete_property(property_id):
    property_obj = Property.query.get_or_404(property_id)
    property_obj.is_active = False  # Мягкое удаление - объект пропадает у клиента
    db.session.commit()
    return jsonify({'success': True, 'message': 'Объявление удалено'})


@app.route('/api/admin/banners', methods=['GET'])
def admin_get_banners():
    banners = Banner.query.order_by(Banner.page, Banner.order).all()
    result = [{
        'id': b.id,
        'image': get_full_url(b.image_path),
        'title': b.title,
        'link': b.link,
        'page': b.page,
        'target_property_id': b.target_property_id,
        'target_jk': b.target_jk,
        'market': b.market,
        'type': b.type,
        'order': b.order,
        'is_active': b.is_active,
        'created_at': b.created_at.isoformat()
    } for b in banners]
    return jsonify(result)


@app.route('/api/admin/banners', methods=['POST'])
def admin_create_banner():
    if 'image' not in request.files:
        return jsonify({'error': 'Изображение не загружено'}), 400

    file = request.files['image']
    path = save_file(file)
    if not path:
        return jsonify({'error': 'Ошибка загрузки'}), 400

    page = request.form.get('page', 'home')
    banner = Banner(
        image_path=path,
        title=request.form.get('title'),
        link=request.form.get('link'),
        page=page,
        target_property_id=request.form.get('target_property_id', type=int) if page == 'thailand' else None,
        target_jk=request.form.get('target_jk') if page == 'jk' else None,
        market=request.form.get('market') if page == 'jk' else None,
        type=request.form.get('type') if page == 'jk' else None,
        order=int(request.form.get('order', 0)),
        is_active=True
    )
    db.session.add(banner)
    db.session.commit()
    return jsonify({'success': True, 'id': banner.id, 'message': 'Баннер создан'})


@app.route('/api/admin/banners/<int:banner_id>', methods=['PUT'])
def admin_update_banner(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    if 'image' in request.files:
        file = request.files['image']
        path = save_file(file)
        if path:
            banner.image_path = path

    banner.title = request.form.get('title', banner.title)
    banner.link = request.form.get('link', banner.link)
    banner.page = request.form.get('page', banner.page)
    banner.target_property_id = request.form.get('target_property_id', banner.target_property_id, type=int)
    banner.target_jk = request.form.get('target_jk', banner.target_jk)
    banner.market = request.form.get('market', banner.market)
    banner.type = request.form.get('type', banner.type)
    banner.order = request.form.get('order', banner.order, type=int)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Баннер обновлен'})


@app.route('/api/admin/banners/<int:banner_id>', methods=['DELETE'])
def admin_delete_banner(banner_id):
    banner = Banner.query.get_or_404(banner_id)
    banner.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': 'Баннер удален'})


@app.route('/api/admin/sell-requests', methods=['GET'])
def admin_get_sell_requests():
    search = request.args.get('search')
    query = SellRequest.query.filter_by(is_active=True)
    if search:
        search = f"%{search}%"
        query = query.filter(db.or_(
            SellRequest.request_number.like(search),
            SellRequest.name.like(search),
            SellRequest.phone.like(search),
            SellRequest.address.like(search)
        ))
    requests = query.order_by(SellRequest.created_at.desc()).all()
    result = [{
        'id': r.id,
        'request_number': r.request_number,
        'type': r.type,
        'name': r.name,
        'phone': r.phone,
        'address': r.address,
        'description': r.description,
        'photos': json.loads(r.photos) if r.photos else [],
        'status': r.status,
        'customer_tg_id': r.customer_tg_id,
        'created_at': r.created_at.isoformat()
    } for r in requests]
    return jsonify(result)


@app.route('/api/admin/orders', methods=['GET'])
def admin_get_orders():
    search = request.args.get('search')
    query = Order.query.filter_by(is_active=True)
    if search:
        search = f"%{search}%"
        query = query.filter(db.or_(
            Order.order_number.like(search),
            Order.customer_name.like(search),
            Order.customer_phone.like(search)
        ))
    orders = query.order_by(Order.created_at.desc()).all()
    result = [{
        'id': o.id,
        'order_number': o.order_number,
        'items': json.loads(o.items),
        'customer_name': o.customer_name,
        'customer_phone': o.customer_phone,
        'customer_tg_id': o.customer_tg_id,
        'status': o.status,
        'created_at': o.created_at.isoformat()
    } for o in orders]
    return jsonify(result)


@app.route('/api/admin/sell-requests/<int:request_id>', methods=['DELETE'])
def admin_delete_sell_request(request_id):
    sell_request = SellRequest.query.get_or_404(request_id)
    sell_request.is_active = False  # Мягкое удаление - заявка пропадает у клиента
    db.session.commit()
    return jsonify({'success': True, 'message': 'Заявка удалена'})


@app.route('/api/admin/orders/<int:order_id>', methods=['DELETE'])
def admin_delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.is_active = False  # Мягкое удаление - заказ пропадает у клиента
    db.session.commit()
    return jsonify({'success': True, 'message': 'Заказ удален'})


@app.route('/api/admin/sell-requests/<int:request_id>/status', methods=['PUT'])
def admin_update_sell_request_status(request_id):
    sell_request = SellRequest.query.get_or_404(request_id)
    data = request.get_json()
    if 'status' in data:
        sell_request.status = data['status']
        db.session.commit()

        # Отправляем уведомление в ТГ при изменении статуса
        if data['status'] in ['В работе', 'Завершена']:
            send_telegram_message(
                f"📝 *Заявка* #{sell_request.request_number}\n"
                f"Статус изменен: {data['status']}\n"
                f"Клиент: {sell_request.name}\n"
                f"Телефон: {sell_request.phone}"
            )

        return jsonify({'success': True, 'message': 'Статус обновлен'})
    return jsonify({'error': 'Не указан статус'}), 400


@app.route('/api/admin/orders/<int:order_id>/status', methods=['PUT'])
def admin_update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    if 'status' in data:
        order.status = data['status']
        db.session.commit()

        # Отправляем уведомление в ТГ при изменении статуса
        if data['status'] in ['В работе', 'Завершен', 'Отправлен клиенту']:
            send_telegram_message(
                f"📦 *Заказ* #{order.order_number}\n"
                f"Статус изменен: {data['status']}\n"
                f"Клиент: {order.customer_name or '—'}\n"
                f"Телефон: {order.customer_phone or '—'}"
            )

        return jsonify({'success': True, 'message': 'Статус обновлен'})
    return jsonify({'error': 'Не указан статус'}), 400


# === СТАТИЧЕСКИЕ ФАЙЛЫ ===

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/admin')
def admin_page():
    return render_template('admin.html')


@app.route('/')
def index_page():
    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)  # Убрали debug=True!
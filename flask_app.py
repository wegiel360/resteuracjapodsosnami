from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import json
import random
import os
import uuid
import subprocess
from datetime import datetime
from pathlib import Path
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')
# ... (rest of the file stays same until database initialization)
app.config['SECRET_KEY'] = 'restaurant_sosny_secret'
app.json.ensure_ascii = False

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR / 'bazadanych.json'

MENU_EN = {
    'Pierogi Ruskie': 'Russian Dumplings', 'Schabowy': 'Breaded Pork Chop',
    'Rosół': 'Chicken Soup', 'Placki Ziemniaczane': 'Potato Pancakes',
    'Bigos': "Hunter's Stew", 'Kotlet Mielony': 'Minced Pork Cutlet',
    'Kompot': 'Compote', 'Szarlotka': 'Apple Pie', 'Tortilla': 'Tortilla',
    'Zimna Woda': 'Cold Water', 'Frytki': 'Fries', 'Mleko': 'Milk',
    'Panini': 'Panini', 'Jajko Smażone': 'Fried Egg', 'Woda': 'Water'
}
CAT_EN = {
    'Dania Główne': 'Main Courses', 'Zupy': 'Soups', 'Napoje': 'Drinks',
    'Desery': 'Desserts', 'Przystawki': 'Starters', 'Inne': 'Other',
}
EXTRA_EN = {
    'Ketchup': 'Ketchup', 'Musztarda': 'Mustard', 'Majonez': 'Mayonnaise',
    'Sos czosnkowy': 'Garlic sauce', 'Sos': 'Sauce', 'Keczap': 'Ketchup',
    'Szczypiorek': 'Chives', 'Cebula': 'Onion', 'Ogórek': 'Cucumber',
    'Sałatka': 'Salad', 'Papryka': 'Pepper', 'Pieprz': 'Pepper',
    'Sól': 'Salt', 'Czosnek': 'Garlic', 'Cytryna': 'Lemon', 'Cukier': 'Sugar',
    'Śmietana': 'Sour cream', 'Brak': 'None', 'Parówka': 'Sausage',
    '2 parówki': '2 sausages', 'ser cheddar': 'cheddar cheese', 'Mascarpone': 'Mascarpone'
}

PORTIONS_EN = {
    '1 porcja': '1 portion', '2 porcje': '2 portions', '3 porcje': '3 portions', 
    'Duża porcja': 'Large portion', 'Mała porcja': 'Small portion', 'Pól porcji': 'Half portion'
}

def generate_order_number():
    return str(random.randint(101, 999))

_db_cache = None
_db_mtime = 0
_dzwonek_flag = False

def load_database():
    global _db_cache, _db_mtime
    try:
        mtime = os.path.getmtime(DATABASE_FILE)
        if _db_cache is not None and mtime <= _db_mtime:
            return _db_cache
    except OSError:
        pass

    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _db_mtime = os.path.getmtime(DATABASE_FILE)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback tworzy wyłącznie czyste struktury bez sztywnego menu
        data = {
            "orders": [], 
            "menu_items": [],
            "portions": ["1 porcja", "2 porcje", "Pól porcji"],
            "extras": ["Sól", "Pieprz", "Ketchup"],
            "custom_message": "Witaj w Barze Węgielstwo!",
            "danie_dnia": ""
        }
        _db_mtime = 0

    # Szybka normalizacja brakujących pól robiona TYLKO przy odczycie z dysku
    if 'custom_message' not in data: data['custom_message'] = "Witaj w Barze Węgielstwo!"
    if 'portions' not in data: data['portions'] = []
    if 'extras' not in data: data['extras'] = []
    if 'receipt_counter' not in data: data['receipt_counter'] = 0
    
    for order in data.get('orders', []):
        if 'order_number' not in order: order['order_number'] = generate_order_number()
        if 'status' not in order: order['status'] = 'Zamówione'
        
    for item in data.get('menu_items', []):
        if 'category' not in item: item['category'] = 'Inne'
        
    _db_cache = data
    return data

def get_db():
    return load_database()

def save_database(data):
    global _db_cache, _db_mtime
    _db_cache = data
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    try:
        _db_mtime = os.path.getmtime(DATABASE_FILE)
    except OSError:
        _db_mtime = 0

def perform_internal_cleanup():
    """Szybkie czyszczenie wywoływane lokalnie przy starcie aplikacji"""
    try:
        db = load_database()
        now = datetime.now()
        cutoff = now.timestamp() - 24*3600
        db['orders'] = [o for o in db.get('orders', []) if not o.get('timestamp') or datetime.fromisoformat(o['timestamp']).timestamp() > cutoff]
        db['last_cleanup'] = now.isoformat()
        save_database(db)
    except Exception:
        pass

def zapisz_paragon(order):
    PARAGON_DIR = Path(r'C:\Users\wegiel\Pictures\kitchen\paragony')
    PARAGON_DIR.mkdir(exist_ok=True)
    
    db = load_database()
    counter = db.get('receipt_counter', 0)
    numer = f"{counter:04d}"
    db['receipt_counter'] = counter + 1
    save_database(db)
    
    filename = f"paragon_{numer}.txt"
    filepath = PARAGON_DIR / filename
    
    receipt_content = []
    receipt_content.append("Bar Węgielstwo")
    receipt_content.append("------------------------------------")
    receipt_content.append(f"Data: {datetime.fromisoformat(order['timestamp']).strftime('%d.%m.%Y %H:%M:%S')}")
    receipt_content.append(f"Numer: {numer}")
    for item in order.get('items', []):
        name = item.get('name', 'Pozycja')
        portion = item.get('portion', '')
        receipt_content.append(f"{name} ({portion}) ...... 0,00 zł")
    receipt_content.append("------------------------------------")
    receipt_content.append("**DO ZAPŁACENIA:** 0,00 zł")
    receipt_content.append("**Płatność:** Brak")
    receipt_content.append("------------------------------------")
    receipt_content.append("Dziękujemy za wizytę!")
    
    full_text = "\n".join(receipt_content)
    
    print(f"--- [Paragon] Generowanie TXT nr {numer} ---")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"[Paragon] Sukces! Paragon {filename} zapisany.")
    except Exception as e:
        print(f"[Paragon] BŁĄD zapisu: {e}")
        
    return full_text

# ----- Pages -----

@app.route('/')
@app.route('/tablica')
def tablica():
    return render_template('tablica.html')

@app.route('/zamow')
def zamow():
    return render_template('zamow.html')

@app.route('/zamow/en')
def zamow_en():
    return render_template('zamow.html', lang='en')

@app.route('/manage')
def manage():
    return render_template('manage.html')

@app.route('/bazadanych.json')
def database_json():
    return jsonify(get_db())


# ----- Orders API -----

@app.route('/api/orders', methods=['GET', 'POST'])
def api_orders():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Brak danych zamówienia'}), 400
        
        db = load_database()
        order = {
            'id': str(uuid.uuid4()),
            'items': data.get('items', []),
            'status': 'Zamówione',
            'order_number': generate_order_number(),
            'customer_name': data.get('customer_name', 'Gość'),
            'timestamp': datetime.now().isoformat(),
            'notes': data.get('notes', '')
        }
        db['orders'].append(order)
        save_database(db)
        receipt = zapisz_paragon(order)
        return jsonify({'success': True, 'order': order, 'receipt': receipt}), 201
        
    return jsonify(get_db().get('orders', []))

@app.route('/api/orders/clear', methods=['DELETE'])
def api_orders_clear():
    db = load_database()
    db['orders'] = []
    save_database(db)
    return jsonify({'success': True})

@app.route('/api/orders/<order_id>', methods=['PUT', 'DELETE'])
def api_order(order_id):
    db = load_database()
    orders_list = db.get('orders', [])
    
    idx = next((i for i, o in enumerate(orders_list) if o['id'] == order_id), None)
    if idx is None:
        return jsonify({'error': 'Zamówienie nie znalezione'}), 404
        
    if request.method == 'PUT':
        data = request.get_json() or {}
        if 'status' in data:
            orders_list[idx]['status'] = data['status']
        if 'reason' in data:
            orders_list[idx]['reason'] = data['reason']
        save_database(db)
        return jsonify({'success': True, 'order': orders_list[idx]})
        
    elif request.method == 'DELETE':
        orders_list.pop(idx)
        save_database(db)
        return jsonify({'success': True})


# ----- Menu API -----

@app.route('/api/menu', methods=['GET', 'POST'])
def api_menu():
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Brak nazwy potrawy'}), 400
            
        db = load_database()
        item = {
            'name': data['name'], 
            'emoji': data.get('emoji', '\U0001f37d'),
            'available': data.get('available', True),
            'category': data.get('category', 'Inne')
        }
        db['menu_items'].append(item)
        save_database(db)
        return jsonify({'success': True, 'item': item}), 201
        
    items = get_db().get('menu_items', [])
    if request.args.get('lang') == 'en':
        return jsonify([
            {**i, 'name': MENU_EN.get(i['name'], i['name']), 'category': CAT_EN.get(i.get('category', ''), i.get('category', ''))} 
            for i in items
        ])
    return jsonify(items)

@app.route('/api/menu/<name>', methods=['PUT', 'DELETE'])
def api_menu_item(name):
    db = load_database()
    menu_list = db.get('menu_items', [])
    
    idx = next((i for i, m in enumerate(menu_list) if m['name'] == name), None)
    if idx is None:
        return jsonify({'error': 'Potrawa nie znaleziona'}), 404
        
    if request.method == 'PUT':
        data = request.get_json() or {}
        for key in ['name', 'emoji', 'available', 'category']:
            if key in data:
                menu_list[idx][key] = data[key]
        save_database(db)
        return jsonify({'success': True, 'item': menu_list[idx]})
        
    elif request.method == 'DELETE':
        menu_list.pop(idx)
        save_database(db)
        return jsonify({'success': True})


# ----- Portions & Extras -----

@app.route('/api/portions')
def api_portions():
    portions = get_db().get('portions', [])
    if request.args.get('lang') == 'en':
        portions = [PORTIONS_EN.get(p, p) for p in portions]
    return jsonify({'portions': portions})

@app.route('/api/extras', methods=['GET', 'POST'])
def api_extras():
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Brak nazwy'}), 400
            
        name = data['name'].strip()
        if not name:
            return jsonify({'error': 'Nazwa nie może być pusta'}), 400
            
        db = load_database()
        if 'extras' not in db: 
            db['extras'] = []
            
        if any((e['name'] == name if isinstance(e, dict) else e == name) for e in db['extras']):
            return jsonify({'error': 'Dodatek już istnieje'}), 400
            
        db['extras'].append({'name': name, 'emoji': data.get('emoji', ''), 'available': True})
        save_database(db)
        return jsonify({'success': True, 'extras': db['extras']}), 201
        
    raw = get_db().get('extras', [])
    extras = [e if isinstance(e, dict) else {'name': e, 'emoji': '', 'available': True} for e in raw]
    if request.args.get('lang') == 'en':
        extras = [{**e, 'name': EXTRA_EN.get(e['name'], e['name'])} for e in extras]
    return jsonify({'extras': extras})

@app.route('/api/extras/<name>', methods=['PUT', 'DELETE'])
def api_extra(name):
    db = load_database()
    if 'extras' not in db:
        return jsonify({'error': 'Nie znaleziono'}), 404
        
    idx = next((i for i, e in enumerate(db['extras']) if (e['name'] if isinstance(e, dict) else e) == name), None)
    if idx is None:
        return jsonify({'error': 'Nie znaleziono'}), 404
        
    if request.method == 'PUT':
        data = request.get_json() or {}
        if not isinstance(db['extras'][idx], dict):
            db['extras'][idx] = {'name': db['extras'][idx], 'emoji': '', 'available': True}
        if 'available' in data:
            db['extras'][idx]['available'] = data['available']
        save_database(db)
        return jsonify({'success': True, 'extras': db['extras']})
        
    elif request.method == 'DELETE':
        db['extras'].pop(idx)
        save_database(db)
        return jsonify({'success': True, 'extras': db['extras']})


# ----- Dzwonek (manual bell) -----

@app.route('/api/dzwonek', methods=['GET', 'POST'])
def api_dzwonek():
    global _dzwonek_flag
    if request.method == 'POST':
        _dzwonek_flag = True
        return jsonify({'success': True})
    v = _dzwonek_flag
    _dzwonek_flag = False
    return jsonify({'ring': v})


# ----- Message / Misc -----

@app.route('/api/message', methods=['GET', 'POST'])
def api_message():
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Brak wiadomości'}), 400
        db = load_database()
        db['custom_message'] = data['message']
        save_database(db)
        return jsonify({'success': True, 'message': db['custom_message']})
        
    return jsonify({'message': get_db().get('custom_message', '')})

@app.route('/api/danie-dnia', methods=['GET', 'POST'])
def api_danie_dnia():
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'danie' not in data:
            return jsonify({'error': 'Brak dania'}), 400
        db = load_database()
        db['danie_dnia'] = data['danie']
        save_database(db)
        return jsonify({'success': True, 'danie': db['danie_dnia']})
        
    return jsonify({'danie': get_db().get('danie_dnia', '')})

@app.route('/api/cleanup', methods=['POST'])
def api_cleanup():
    db = load_database()
    now = datetime.now()
    cutoff = now.timestamp() - 24*3600
    before = len(db.get('orders', []))
    db['orders'] = [o for o in db.get('orders', []) if not o.get('timestamp') or datetime.fromisoformat(o['timestamp']).timestamp() > cutoff]
    deleted = before - len(db['orders'])
    db['last_cleanup'] = now.isoformat()
    save_database(db)
    return jsonify({'deleted': deleted, 'last_run': db['last_cleanup']})


application = app

if __name__ == '__main__':
    perform_internal_cleanup()
    app.run(host='0.0.0.0', port=6969, debug=False)
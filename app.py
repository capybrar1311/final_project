from flask import Flask, render_template, request, redirect, url_for
import datetime as dt
from datetime import date
from datetime import datetime

import sqlite3
app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/events/')
def events():
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT NOT NULL
        )
    ''')
    today = date.today()
    today = today.strftime("%Y-%m-%d")
    cursor.execute('''
        SELECT events.id, events.name, events.date, events.time, event_type.name as t_name FROM events
        LEFT JOIN event_type_event ON events.id = event_type_event.event_id
        LEFT JOIN event_type ON event_type_event.event_type_id = event_type.id
        WHERE events.date > ? AND events.deleted_at IS NULL
        ORDER BY events.date
        ''', (today,))
    events = cursor.fetchall()
    data_base.commit()
    data_base.close()
    return render_template('events/event_list.html', events=events)

@app.route('/event_detail/<int:id>')
def event_detail(id):
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row

    cursor.execute(''' SELECT * FROM events WHERE id == ? ''', (id,))
    event = cursor.fetchall()

    cursor.execute('''
            SELECT *
            FROM act
            WHERE (event_id == ?) AND (deleted_at IS NULL) ORDER BY act.number
            ''', (id,))
    acts = cursor.fetchall()
    data_base.close()
    return render_template('acts/event_acts_list.html', event=event, acts=acts, event_id=id)

@app.route('/add_event/', methods=['GET', 'POST'])
def add_event():

    if request.method == 'POST':
        data_base = sqlite3.connect('events.db')
        cursor = data_base.cursor()
        cursor.row_factory = sqlite3.Row

        name = request.form.get('name')
        request_date = request.form.get('date')
        time = request.form.get('time')
        event_type_name = request.form.get('event_type_name')
        event_type_id = 2

        cursor.execute('''
        SELECT id from event_type WHERE name is ?''', (event_type_name,))
        event_type_id = cursor.fetchone()
        event_type_id = int(*event_type_id)

        today = date.today()
        today = today.strftime("%Y-%m-%d")
        created_at = today
        updated_at = today

        cursor.execute('''
        INSERT INTO events (name, date, time, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, request_date, time, created_at, updated_at))

        cursor.execute(''' 
        INSERT INTO event_type_event (event_type_id, event_id)
        VALUES (?, ?)
        ''', (event_type_id, cursor.lastrowid))

        data_base.commit()
        data_base.close()
        return redirect(url_for('events'))
    return render_template('events/add_event.html')

@app.route('/delete_event/<int:event_id>', methods=['GET', 'POST'])
def delete_event(event_id):

    if request.method == 'POST':
        data_base = sqlite3.connect('events.db')
        cursor = data_base.cursor()
        cursor.row_factory = sqlite3.Row

        cursor.execute('''
            UPDATE events
            SET deleted_at = ?
            WHERE id = ?
                
        ''', (datetime.now(), event_id))
        data_base.commit()
        data_base.close()
        return redirect(url_for('events'))
    return render_template('events/delete_event.html', event_id=event_id)

@app.route('/acts/')
def acts():

    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS act (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number integer NOT NULL,
            name TEXT NOT NULL,
            performer TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT default NULL,
            event_id integer,
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
    ''')
    data_base.commit()

    if request.method == 'GET':
        cursor.execute('''
            SELECT * FROM act
            ''')
        acts = cursor.fetchall()
        data_base.commit()
        data_base.close()
        return render_template('acts/act_list.html', acts=acts)
    data_base.close()


@app.route('/add_act/<int:id>', methods=['GET', 'POST'])
def add_act(id):

    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row

    if request.method == 'POST':

        number = request.form.get('number')
        name = request.form.get('name')
        performer = request.form.get('performer')
        today = date.today()
        today = today.strftime("%Y-%m-%d")

        created_at = today
        updated_at = today

        try:
            cursor.execute('''
                INSERT INTO act (number, name, performer, created_at, updated_at, event_id)
                VALUES (?, ?, ?, ?, ?, ?)''', (number, name, performer, created_at, updated_at, id))
            data_base.commit()

        except Exception as e:
            data_base.close()
        data_base.close()
        return redirect(url_for('event_detail', id=id))

    return render_template('acts/add_act.html')

@app.route('/act_detail/<int:id>', methods=['GET', 'POST'])
def act_detail(id):
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('''
        SELECT * FROM act WHERE id is ? AND event_id is NOT NULL
        ''', (id,))
    act = cursor.fetchone()

    if request.method == 'POST':
        cursor.execute('''
            UPDATE act SET number = ?, name = ?, performer = ?, updated_at = ? WHERE id = ?
            ''', (request.form.get('number'), request.form.get('name'), request.form.get('performer'), datetime.now(), id))
        data_base.commit()
        data_base.close()
        return redirect(url_for('event_detail', id=act['event_id']))
    return render_template('acts/add_act.html', act=act, args=request.args)

@app.route('/delete_act/<int:id>', methods=['GET', 'POST'])
def delete_act(id):
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('''
        SELECT event_id FROM act WHERE id = ?
        ''', (id,))
    act = cursor.fetchone()
    if request.method == 'POST':
        cursor.execute('''
            UPDATE act SET deleted_at = ? WHERE id = ?
            ''', (datetime.now(), id))
        data_base.commit()
        data_base.close()
        return redirect(url_for('event_detail', id=int(*act)))
    return redirect(url_for('event_detail', id=int(*act)))

@app.route('/event_type_list/', methods=['GET'])
def event_type_list():
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute(''' CREATE TABLE IF NOT EXISTS event_type (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL unique,
        description TEXT NOT NULL default "---")
                   ''')

    cursor.execute('''
        SELECT * FROM event_type
        ''')
    event_types = cursor.fetchall()
    data_base.close()
    return render_template('event_types/event_type_list.html', event_types=event_types)

@app.route('/add_event_type/', methods=['GET', 'POST'])
def add_event_type():

    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row

    if request.method == 'POST':
        cursor.execute('''
            INSERT INTO event_type (name, description) VALUES (?, ?)
            ''', (request.form.get('name'), request.form.get('description')))
        data_base.commit()
        data_base.close()
        return redirect(url_for('event_type_list'))
    data_base.close()
    return render_template('event_types/add_event_type.html')

@app.route('/delete_event_type/<int:id>', methods=['GET', 'POST'])
def delete_event_type(id):

    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row

    cursor.execute('''
        DELETE FROM event_type WHERE id = ?
        ''', (id,))
    data_base.commit()
    data_base.close()
    return redirect(url_for('event_type_list'))

@app.route('/event_type_detail/<int:type_id>', methods=['GET', 'POST'])
def event_type_detail(type_id):

    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('''
        SELECT * FROM event_type WHERE id = ?
        ''', (type_id,))

    event_type = cursor.fetchone()
    if request.method == 'POST':
        cursor.execute('''
            UPDATE event_type SET name = ?, description = ? WHERE id = ?
            ''', (request.form.get('name'), request.form.get('description'), type_id))
        data_base.commit()
        data_base.close()
        return redirect(url_for('event_type_list'))
    data_base.close()
    return render_template('event_types/add_event_type.html', event_type=event_type)

@app.route('/set_event_type/<int:type_id>', methods=['GET', 'POST'])
def set_event_type(type_id):

    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    #TODO приделать обновление типа события
    #TODO прикрутить JOIN c event_type чтобы доставать
    if request.method == 'POST':
        cursor.execute('''
            UPDATE event_type_event SET type_id = ? WHERE event_id = ?
            ''', (type_id, request.form.get('event_id')))
        data_base.commit()
        data_base.close()
        return redirect(url_for('event_detail')
def index():
    return render_template('index.html')

# НЕ СТИРАТЬ
if __name__ == '__main__':
    app.run(debug=True)
    print('sskjufhis')
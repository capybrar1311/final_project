from flask import Flask, render_template, request, redirect, url_for
import datetime as dt
from datetime import date
from datetime import datetime

import sqlite3
app = Flask(__name__)

class Act:
    act_data = sqlite3.Row
    act_performers = sqlite3.Row


@app.route('/')
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
    cursor.execute(''' SELECT event_type.name as et_name,
                                    event_type.id as et_id
                                    FROM event_type 
                                LEFT JOIN event_type_event ON event_type.id = event_type_event.event_type_id
                                LEFT JOIN events ON event_type_event.event_id = events.id
                                WHERE events.id == ?
                                 ''', (id,))
    current_event_type = cursor.fetchone()

    cursor.execute(''' SELECT * FROM event_type ''')
    event_types = cursor.fetchall()

    cursor.execute('''
            SELECT act.id as act_id, 
                   act.name as act_name, 
                   act.number as act_number, 
                   act.act_type_id as act_type_id,
                   act_type.name as act_type_name
            FROM act
            JOIN act_type ON act.act_type_id = act_type.id
            WHERE (event_id == ?) AND (deleted_at IS NULL) ORDER BY act.number
            ''', (id,))
    acts_data = cursor.fetchall()
    performers_data = []
    for act in acts_data:
        cursor.execute('''  SELECT *
                            FROM performer_act
                            JOIN performer ON performer_act.performer_id = performer.id
                            WHERE act_id is ?
                       ''',( act['act_id'],))
        performers_data.append(cursor.fetchall())
    data_base.close()

    acts = []
    for act in acts_data:
        acts.append([act])
    for a in acts:
        a.append(performers_data[acts.index(a)])
    return render_template('acts/event_acts_list.html',
                           event=event,
                           acts=acts,
                           event_types=event_types,
                           current_event_type=current_event_type,
                           event_id=id)

@app.route('/add_event/', methods=['GET', 'POST'])
def add_event():
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute(''' SELECT * FROM event_type ''')
    event_types = cursor.fetchall()

    if request.method == 'POST':

        name = request.form.get('name')
        request_date = request.form.get('date')
        time = request.form.get('time')
        event_type_name = request.form.get('event_type_name')
        event_type_id = request.form.get('type_id')

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
    return render_template('events/add_event.html', event_types=event_types)

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
        if request.method == 'POST':
            cursor.execute('''
                           UPDATE act
                           SET number      = ?,
                               name        = ?,
                               updated_at  = ?,
                               act_type_id = ?
                           WHERE id = ?
                           ''', (request.form.get('number'),
                                 request.form.get('name'),
                                 datetime.now(),
                                 request.form.get('act_type_id'),
                                 id))
            if current_performers:
                for p_id in p_ids:
                    cursor.execute('''
                                   INSERT INTO performer_act (act_id, performer_id)
                                   VALUES (?, ?) ON CONFLICT (act_id, performer_id) DO NOTHING
                                   ''', (id, p_id))
            data_base.commit()
            data_base.close()
            return redirect(url_for('event_detail', id=act['event_id']))
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
    cursor.execute('''
    SELECT * from performer
    ''')
    performers = cursor.fetchall()

    p_ids = list(int(i) for i in request.form.getlist('performer_ids[]'))
    placeholders = ','.join('?' * len(p_ids))
    sql = f'''
                   SELECT * from performer WHERE id in ({placeholders})
                   '''
    cursor.execute(sql, p_ids)
    current_performers = cursor.fetchall()

    cursor.execute('''
        SELECT * FROM act_type
        ''')
    act_types = cursor.fetchall()

    cursor.execute('''
        SELECT * FROM act_type WHERE id = ?
        ''', (request.form.get('act_type_id'),))
    current_act_type = cursor.fetchone()

    if request.method == 'POST':

        p_ids = list(int(i) for i in request.form.getlist('performer_ids[]'))

        placeholders = ','.join('?' * len(p_ids))
        sql = f'''
                SELECT * from performer WHERE id in ({placeholders})
                '''
        cursor.execute(sql, p_ids)
        current_performers = cursor.fetchall()

        cursor.execute('''
            UPDATE act SET number = ?, name = ?, updated_at = ?, act_type_id = ? WHERE id = ?
            ''', (request.form.get('number'),
                  request.form.get('name'),
                  datetime.now(),
                  request.form.get('act_type_id'),
                  id))
        if current_performers:
            for p_id in p_ids:
                cursor.execute('''
                    INSERT INTO performer_act (act_id, performer_id) VALUES (?, ?)
                    ''', (id, p_id))
        data_base.commit()
        data_base.close()
        return redirect(url_for('event_detail', id=act['event_id']))
    return render_template('acts/add_act.html',
                           act=act,
                           act_types=act_types,
                           current_act_type=current_act_type,
                           args=request.args,
                           performers=performers,
                           current_performers=current_performers)

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

@app.route('/set_event_type/<int:id>', methods=['GET', 'POST'])
def set_event_type(id):
    type_id = request.form.get('type_id')
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    #TODO приделать обновление типа события
    #TODO прикрутить JOIN c event_type чтобы доставать

    cursor.execute('''
        SELECT * FROM event_type_event WHERE event_id = ?
        ''', (id,))
    event_type_event = cursor.fetchone()

    if event_type_event is None and request.method == 'POST':
        cursor.execute('''
            INSERT INTO event_type_event (event_id, event_type_id) VALUES (?, ?)
            ''', (id, type_id))
        data_base.commit()
        data_base.close()
        return redirect(url_for('event_detail', id=id))

    if request.method == 'POST' and event_type_event is not None:
        cursor.execute('''
            UPDATE event_type_event SET event_type_id = ? WHERE event_id = ?
            ''', (type_id, id))
        data_base.commit()
        data_base.close()
        return redirect(url_for('event_detail', id=id))
    data_base.close()
    return render_template(url_for('event_detail', id=id))


@app.route('/act_types/')
def act_type_list():
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('''
        SELECT * FROM act_type
        ''')
    act_types = cursor.fetchall()
    data_base.close()
    return render_template('act_types/act_type_list.html', act_types=act_types)

@app.route('/add_act_type', methods=['GET', 'POST'])
def add_act_type():
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row

    if request.method == 'POST':
        cursor.execute('''
                       INSERT INTO act_type (name, description)
                       VALUES (?, ?)
                       ''', (request.form.get('name'), request.form.get('description')))
        data_base.commit()
        data_base.close()
        return redirect(url_for('act_type_list'))
    data_base.close()
    return render_template('act_types/add_act_type.html')

@app.route('/act_type_detail/<int:type_id>', methods=['GET', 'POST'])
def act_type_detail(type_id):
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('''
        SELECT * FROM act_type WHERE id = ?
        ''', (type_id,))
    act_type = cursor.fetchone()
    if request.method == 'POST' and act_type is not None:
        cursor.execute('''
            UPDATE act_type SET name = ?, description = ? WHERE id = ?
            ''', (request.form.get('name'), request.form.get('description'),type_id))
        data_base.commit()
        data_base.close()
        return redirect(url_for('act_type_list'))
    data_base.close()
    return render_template('act_types/add_act_type.html', act_type=act_type)

@app.route('/delete_act_type/<int:id>', methods=['GET', 'POST'])
def delete_act_type(id):

    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('''
        DELETE FROM act_type WHERE id = ?
        ''', (id,))
    data_base.commit()
    data_base.close()
    return redirect(url_for('act_type_list'))


@app.route('/performer_list/')
def performer_list():

    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('''
        SELECT * FROM performer
        ''')
    performers = cursor.fetchall()
    data_base.close()
    return render_template('performers/performer_list.html', performers=performers)

@app.route('/add_performer/', methods=['GET', 'POST'])
def add_performer():
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row

    if request.method == 'POST':

        cursor.execute('''
                       INSERT INTO performer (first_name, last_name, middle_name, location_city)
                       VALUES (?, ?, ?, ?)
                       ''', (request.form.get('first_name'), request.form.get('last_name'), request.form.get('middle_name'), request.form.get('location_city')))
        data_base.commit()
        data_base.close()
        return redirect(url_for('performer_list'))
    data_base.close()
    return render_template('performers/add_performer.html')

@app.route('/performer_detail/<int:id>', methods=['GET', 'POST'])
def performer_detail(id):
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('''
        SELECT * FROM performer WHERE id = ?
        ''', (id,))
    performer = cursor.fetchone()
    if request.method == 'POST' and performer is not None:
        cursor.execute('''
            UPDATE performer SET first_name = ?, last_name = ?, middle_name = ?, location_city = ? WHERE id = ?
            ''', (request.form.get('first_name'), request.form.get('last_name'), request.form.get('middle_name'), request.form.get('location_city'), id))
        data_base.commit()
        data_base.close()
        return redirect(url_for('performer_list'))
    data_base.close()
    return render_template('performers/add_performer.html', performer=performer)

@app.route('/delete_performer/<int:id>', methods=['GET', 'POST'])
def delete_performer(id):
    data_base = sqlite3.connect('events.db')
    cursor = data_base.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('''
        DELETE FROM performer WHERE id = ?
        ''', (id,))
    data_base.commit()
    data_base.close()
    return redirect(url_for('performer_list'))
# НЕ СТИРАТЬ
if __name__ == '__main__':
    app.run(debug=True)
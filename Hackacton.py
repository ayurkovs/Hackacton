from flask import Flask, render_template, session, redirect, url_for, request, g
import sqlite3

app = Flask(__name__)

SECRET_KEY = 'development key3'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('Sportner.db')
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/register')
def register():
    return render_template('register_page.html')


@app.route('/my_events')
def my_events():
    if session.get('logged_in'):
        events_data = []
        registrations = query_db('SELECT * FROM Registrations WHERE UserID={}'.format(session.get('user_id')))
        for reg in registrations:
            event = query_db(' SELECT * FROM Events WHERE ID={}'.format(reg[2]))
            city_name = query_db('SELECT Name from Cities WHERE ID=\'{}\''.format(event[0][1]), one=True)[0]
            specific_location = event[0][2]
            date = event[0][3]
            max_registers = event[0][4]
            activity = query_db('SELECT Name from Activities WHERE ID=\'{}\''.format(event[0][5]), one=True)[0]
            events_data.append((city_name, specific_location, date, max_registers, activity, reg[3]))
        return render_template('my_events.html', events_data=events_data)
    else:
        return redirect(url_for('login_page'))


@app.route('/')
@app.route('/<activity_id_chosen>/<tags_chosen>')
def main(activity_id_chosen=None, tags_chosen=None):
    if session.get('logged_in'):
        cur = get_db().cursor()

        activities_ids = query_db(
            'SELECT ActivityID FROM FaveActivities WHERE UserID=\'{}\''.format(session.get('user_id')))
        activities_ids = [activity_id[0] for activity_id in activities_ids]

        activities_names = [
            query_db('SELECT Name from Activities WHERE ID=\'{}\''.format(current_activity_id), one=True)[0] for
            current_activity_id in activities_ids]
        activities_ids_and_names = zip(activities_ids, activities_names)

        user_preferences_string = ''
        tags_query = ''
        tags = []
        if activity_id_chosen is not None:
            user_preferences_string = 'ActivityID = \'{}\''.format(activity_id_chosen)
            session['activity_id_chosen'] = activity_id_chosen
            if tags_chosen == '1' or tags_chosen == '2' or tags_chosen == '3' or tags_chosen == '4' or tags_chosen == '5' or tags_chosen == '6' or tags_chosen == '7' or tags_chosen == '8' or tags_chosen == '9' or tags_chosen == '10' or tags_chosen == '11' or tags_chosen == '12' or tags_chosen == '13' or tags_chosen == '14' or tags_chosen == '15' or tags_chosen == '16' or tags_chosen == '17' or tags_chosen == '18':
                session['tags_chosen'].append(tags_chosen)

            if len(session['tags_chosen']) != 0:
                tags_query = ' OR '.join(['TagID = \'{}\''.format(c) for c in session['tags_chosen']])
                tags_query = 'SELECT EventID FROM EventsTags WHERE ' + tags_query
                tags_query = [c[0] for c in query_db(tags_query)]
                if len(tags_query) != 0:
                    tags_query = ['ID = \'{}\''.format(c) for c in tags_query]
                    tags_query = ' OR '.join(tags_query)
                    tags_query = ' AND (' +  tags_query + ')'
                else:
                    tags_query = ' AND 1==0'

            tags = query_db('SELECT ID, Tag FROM Tags WHERE ActivityID=\'{}\''.format(activity_id_chosen))
        else:
            session['activity_id_chosen'] = None
            session['tags_chosen'] = []
            user_preferences_strings = []
            for preference in activities_ids:
                user_preferences_strings.append('ActivityID = \'{}\''.format(preference))
            user_preferences_string = ' OR '.join(user_preferences_strings)

        events_data = []

        events = query_db('SELECT * FROM Events WHERE ' + user_preferences_string + tags_query)
        events_ids = [event[0] for event in events]
        for i in range(len(events)):
            current_users_ids = [c[0] for c in query_db(
                'SELECT UserID FROM Registrations WHERE EventID=\'{}\''.format(events_ids[i]))]
            current_users = []
            for current_user_id in current_users_ids:
                current_users.append(
                    query_db('SELECT UserName from Users WHERE ID=\'{}\''.format(current_user_id), one=True)[0])

            event_tags_ids = [c[0] for c in
                              query_db('SELECT TagID FROM EventsTags WHERE EventID=\'{}\''.format(events_ids[i]))]
            event_tags = [query_db('SELECT Tag from Tags WHERE ID=\'{}\''.format(c))[0][0] for c in event_tags_ids]

            event_id = events[i][0]
            city_name = query_db('SELECT Name from Cities WHERE ID=\'{}\''.format(events[i][1]), one=True)[0]
            specific_location = events[i][2]
            date = events[i][3]
            max_registers = events[i][4]
            activity = query_db('SELECT Name from Activities WHERE ID=\'{}\''.format(events[i][5]), one=True)[0]

            events_data.append(
                (city_name, specific_location, date, max_registers, activity, current_users, event_id, event_tags))

        return render_template('main.html', events_data=events_data, activities_ids_and_names=activities_ids_and_names,
                               tags=tags)
    else:
        return redirect(url_for('login_page'))


@app.route('/register_success', methods=['POST'])
def register_success_handler():
    name = '\'' + request.form['Name'] + '\''
    user_name = '\'' + request.form['Username'] + '\''
    password = '\'' + request.form['Password'] + '\''
    date_of_birth = '\'' + request.form['date_of_birth'] + '\''
    gender = '\'' + request.form['Gender'] + '\''
    email = '\'' + request.form['email'] + '\''
    phone = '\'' + request.form['Phone Number'] + '\''
    city = '\'' + request.form['favourite_cities'] + '\''
    args = ','.join([name, user_name, password, date_of_birth, gender, email, phone])
    query = 'INSERT INTO Users (Name, UserName, Password, Age, Gender, Email, Phone) VALUES ({})'.format(args)
    query_db_no_return_value(query)
    select_user_query = 'SELECT * FROM Users WHERE UserName={}'.format(user_name)
    user_id = query_db(select_user_query)[0][0]
    insert_city(city, user_id)
    insert_activity('1', user_id) if request.form.get('running') == 'on' else None  # should return 'on'
    insert_activity('2', user_id) if request.form.get('walking') == 'on' else None
    insert_activity('3', user_id) if request.form.get('basketball') == 'on' else None
    insert_activity('4', user_id) if request.form.get('soccer') == 'on' else None
    insert_activity('5', user_id) if request.form.get('tennis') == 'on' else None
    insert_activity('6', user_id) if request.form.get('gym') == 'on' else None
    return render_template('register_success.html')


def insert_activity(activity_id, user_id):
    args = ','.join([str(user_id), activity_id])
    query = 'INSERT INTO FaveActivities (UserID, ActivityID) VALUES ({})'.format(args)
    query_db_no_return_value(query)


def insert_city(city_id, user_id):
    args = ','.join([str(user_id), str(city_id)])
    query = 'INSERT INTO RelevantCities (UserID, CityID) VALUES ({})'.format(args)
    query_db_no_return_value(query)


def query_db_no_return_value(query, args=(), one=False):
    db = get_db()
    db.execute(query, args)
    db.commit()


@app.route('/login_page', methods=['GET', 'POST'])
def login_page():
    if session.get('logged_in'):
        return redirect(url_for('main'))

    error = None
    if request.method == 'POST':
        cur = get_db().cursor()
        password = query_db('SELECT Password FROM Users WHERE UserName=\'{}\''.format(request.form['username']),
                            one=True)

        if password is None:
            error = "No user with such user name"
        elif password[0] != request.form['password']:
            error = "password doesn't match user name"
        else:
            session['logged_in'] = True
            session['username'] = request.form['username']
            session['user_id'] = \
                query_db('SELECT ID FROM Users WHERE UserName=\'{}\''.format(request.form['username']), one=True)[0]
            return redirect(url_for('main'))
    return render_template('login_page.html', error=error)


@app.route('/profile')
def profile():
    if session.get('logged_in'):
        # Get username from session
        username = session.get('username')
        user = query_db('SELECT * FROM Users WHERE UserName=\"{}\"'.format(username))
        sports_ids = query_db('SELECT * FROM FaveActivities WHERE UserID=\"{}\"'.format(user[0][0]))
        activities = []
        for id in sports_ids:
            # Get the activities names according to their ids.
            activities.append(query_db('SELECT Name FROM Activities WHERE ID=\'{}\''.format(id[2]))[0][0])
        return render_template('profile.html', user=user, activities=activities)
    else:
        return redirect(url_for('main'))


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login_page'))


@app.route('/create_event')
def create_event():
    if session.get('logged_in'):
        return render_template('create_event.html')
    else:
        return redirect(url_for('login_page'))


@app.route('/event_tags', methods=['POST'])
def event_tags():
    if session.get('logged_in'):
        # Create the event
        activity = '\'' + request.form['activity'] + '\''
        city_id = '\'' + request.form['city'] + '\''
        location = '\'' + request.form['location'] + '\''
        date = request.form['date']
        time = request.form['time']
        max_part = '\'' + request.form['max_part'] + '\''
        user_id = session.get('user_id')
        date_time = "\'{} {}\'".format(date, time + ':00')
        args = ','.join([city_id, location, date_time, max_part, activity])
        query = 'INSERT INTO Events (CityID, Location, DateAndTime, MaxRegisters, ActivityID) VALUES ({})'.format(args)
        query_db_no_return_value(query)
        event_id = query_db('SELECT ID FROM Events ORDER BY ID DESC LIMIT 1')[0][0]
        # Add user as creator and participant
        args = ','.join([str(user_id), str(event_id), '1'])
        query = 'INSERT INTO Registrations (UserID, EventID, Creator) VALUES ({})'.format(args)
        query_db_no_return_value(query)

        # Get relevant tags fot the activity type
        tags = query_db('SELECT * FROM Tags WHERE ActivityID={}'.format(activity))
        return render_template('event_tags.html', tags=tags, num_tags=len(tags), event_id=event_id)

    else:
        return redirect(url_for('login_page'))


@app.route('/event_success', methods=['GET', 'POST'])
def event_success():
    if session.get('logged_in'):

        event_id = request.form['event_id']
        checked_tags = request.form.getlist('checked_tags')
        # add event tags to DB
        for tag in checked_tags:
            args = ','.join([str(event_id), str(tag)])
            query = 'INSERT INTO EventsTags (EventID, TagID) VALUES ({})'.format(args)
            query_db_no_return_value(query)
        return render_template('event_success.html')
    else:
        return redirect(url_for('login_page'))


@app.route('/register_to_event/<event_id>')
def register_to_event(event_id):
    query_db_no_return_value(
        'INSERT INTO Registrations (UserID, EventID, Creator) VALUES ({}, {}, {})'.format(session.get('user_id'),
                                                                                          event_id, 0))
    return redirect(url_for('main'))


if __name__ == '__main__':
    app.config.from_object(__name__)
    app.run()

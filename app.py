import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

assert hasattr(requests, 'get')
assert hasattr(datetime, 'fromtimestamp')


''' 
    html code used - for future modifications
    https://bulma.io/documentation/elements/notification/
    https://bulma.io/documentation/layout/media-object/
'''

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisissecret'
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    name_api = db.Column(db.String(50))
    # name_api2 = db.Column(db.String(48))


def get_weather_data(city):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={ city }&lang=bg&units=metric' + \
          '&appid=271d1234d3f497eed5b1d80a07b3fcd1'  # en - there is error with 'bg' in database is different from
    # received from API
    r = requests.get(url).json()
    print(r)
    return r


@app.route('/')
def index_get():
    cities = City.query.all()

    weather_data = []
    for city in cities:
        r = get_weather_data(city.name)
# TODO use typed city, because if received city is in different language it gives error if try to delete.
# TODO because the send name and received from API can be in different language and same in DB.
# TODO Done - now testing :)
#         r = get_weather_data('Sofia')
        ts = int(f"""{r['sys']['sunrise']}""")
        value = datetime.fromtimestamp(ts)
        sunrise = f"{value:%H:%M:%S}"
        weather = {
            'city': r['name'],
            'temperature': r['main']['temp'],
            'feels_like': r['main']['feels_like'],
            'main': r['weather'][0]['main'],
            'description': r['weather'][0]['description'],
            'wind': r['wind']['speed'],
            'sunrise': sunrise,
            'icon': r['weather'][0]['icon'],
        }
        weather_data.append(weather)

    return render_template('weather.html', weather_data=weather_data)


@app.route('/', methods=['POST'])
def index_post():
    err_msg = ''
    new_city = request.form.get('city')
    if new_city:
        existing_city = City.query.filter_by(name=new_city).first()
        existing_city2 = City.query.filter_by(name_api=new_city).first()
        if not existing_city or not existing_city2:
            new_city_data = get_weather_data(new_city)
            # print(new_city_data)
            if new_city_data['cod'] == 200:
                new_city_obj = City(name=new_city, name_api=new_city_data['name'])
                db.session.add(new_city_obj)
                db.session.commit()
            else:
                err_msg = 'City does not exist in the world!'
        else:
            err_msg = 'City already exist in the database!'
    if err_msg:
        flash(err_msg, 'error')
    else:
        flash('City added successfully!')

    return redirect(url_for('index_get'))


@app.route('/delete/<name>')
def delete_city(name):
    city = City.query.filter_by(name_api=name).first()
    db.session.delete(city)
    db.session.commit()
    flash(f'Successfully deleted { city.name }', 'success')
    return redirect(url_for('index_get'))


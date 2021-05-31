from flask import Flask
from flask import render_template, flash
from flask import request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
import sys
import json
import datetime

app = Flask(__name__)
API_KEY = '516107c9e083439e2d8f6dac62ec882e'
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/(*&^*%'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
db = SQLAlchemy(app)


class Weather(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '<Weather %r>' % self.name


def get_weather_data(city_name: str) -> dict:
    params = {'q': city_name, 'appid': API_KEY, 'units': 'metric'}
    req = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params)
    return json.loads(req.text)


def process_data(json_data: dict) -> dict:
    result = {}
    if json_data['cod'] == 200:
        time = datetime.datetime.utcnow() + datetime.timedelta(seconds=json_data['timezone'])
        time = time.time()
        card_style = 'card day' if 18 > time.hour > 12 else 'card night' \
            if 6 > time.hour else 'card evening-morning'
        result = {
            'temp': json_data['main']['temp'],
            'weather': json_data['weather'][0]['main'],
            'city': json_data['name'],
            'time': time,
            'card_style': card_style,
        }
    return result


@app.route('/', methods=['GET', 'POST'])
def index():
    cities = Weather.query
    content = []
    for city in cities:
        city_content = process_data(get_weather_data(city.name))
        city_content['id'] = city.id
        content.append(city_content)
    return render_template('index.html', content=content)


@app.route('/add', methods=['GET', 'POST'])
def add():
    city = str(request.form['city_name'])
    if not Weather.query.filter_by(name=city).first():
        content = process_data(get_weather_data(city))
        if content:
            db.session.add(Weather(name=city))
            db.session.commit()
        else:
            flash('The city doesn\'t exist!')
    else:
        flash('The city has already been added to the list!')
    return redirect(url_for('index'))


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = Weather.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    return redirect(url_for('index'))


# don't change the following way to run flask:
if __name__ == '__main__':
    db.create_all()
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()

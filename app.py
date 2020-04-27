import time
import pyrebase
import requests
from flask import render_template, request, Flask, session, redirect, url_for
from simplejson import loads
import folium
from datetime import datetime, timedelta

config = {
    "apiKey": "AIzaSyANrB_UTh1rfi1NpN_T4gjbImmIJfqadm0",
    "authDomain": "flaskauth-e4bef.firebaseapp.com",
    "databaseURL": "https://flaskauth-e4bef.firebaseio.com",
    "projectId": "flaskauth-e4bef",
    "storageBucket": "flaskauth-e4bef.appspot.com",
    "messagingSenderId": "556755781928",
    "appId": "1:556755781928:web:adccb8daf63c1f0436681d",
    " measurementId": "G-VH6TVVCGVM"
}

app = Flask(__name__)
firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()
app.secret_key = "light"
app.permanent_session_lifetime = timedelta(hours=12)


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        key = request.form['Key']
        session["key"] = key

        try:
            radio_b = request.form['radio']
            auth.sign_in_with_email_and_password(email, password)
            # session['usr'] = user_id
            # user_id = auth.get_account_info(user['idToken'])
            return redirect(url_for('device'))
        except:
            unsuccessful = 'Please check your credentials'
            return render_template("login.html", umessage=unsuccessful)
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        company = request.form['company']
        phone = request.form['phone']
        name = request.form['name']
        city = request.form['city']
        try:
            auth.create_user_with_email_and_password(email, password)
            successful = 'Account Created'
            db.child(company).child("company").set(company)
            db.child(company).child("name").set(name)
            db.child(company).child("phone").set(phone)
            db.child(company).child("city").set(city)
            return render_template('login.html', smessage=successful)
        except:
            unsuccessful = 'You already have an account'
            return render_template('login.html', umessage=unsuccessful)

    return render_template('signup.html')


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        try:
            email = request.form['email']
            auth.send_password_reset_email(email)
            successful = 'Check your mail !'
            return render_template('login.html', smessage=successful)
        except:
            unseccessful = 'Please enter a valid mail'
            return render_template('reset.html', umessage=unseccessful)
    return render_template('reset.html')


@app.route('/device', methods=['GET', 'POST'])
def device():
    if "key" in session:
        try:
            session.pop("code_selected", None)
            key = session["key"]
            print(key)
            code_ = db.child(key).child("Devices").get().val()
            print(code_)
            return render_template('device.html', code_=code_)
        except:
            unsuccessful = "Invalid Device"
            return render_template('device.html', umessage=unsuccessful)

    return redirect(url_for("login"))


@app.route('/device_info', methods=['GET', 'POST'])
def device_info():
    global temp_k, hum_p, Over, f_temp, f_hum, long, att
    global i, code
    if "key" in session:

        key = session["key"]
        code_selected = request.form.get('code200')
        code = db.child(key).child("Devices").child(code_selected).get().val()
        session["code_selected"] = code
        print(code)
        try:
            name = db.child(key).child('name').get().val()
            city = db.child(key).child('city').get().val()
            h = ('https://api.thingspeak.com/channels/' + code + '/feeds.json?results=2')
            r = requests.get(h)
            for i in range(1):
                i = 0
                r = requests.get(h)
                print(r)
                json_file = r.json()['feeds']
                print(json_file)
                x = (loads(r.text)['feeds'])

                y = x[0]
                temp_k = y['field1']
                hum_p = y['field2']
                f_temp = "%.2f" % float(temp_k)
                f_hum = "%.2f" % float(hum_p)
                if int(float(temp_k)) >= 23:
                    Over = "Temperature is over limit !! : " + temp_k
                Over = ""
                longitude = y['field3']
                latitude = y['field4']
                long = 36.79800033569336
                att = 10.171699523925781
                time.sleep(3)
            m = folium.Map(location=[long, att], zoom_start=12)
            tooltip: str = "Click for more info"
            folium.Marker([long, att],
                          popup='<strong>Device One</strong>',
                          tooltip=tooltip
                          , icon=folium.Icon(color='black', icon='cloud')).add_to(m)
            folium.CircleMarker(
                location=(long, att),
                radius=50,
                popup='Location',
                color='#428bca',
                fill=True,
                fill_color='#428bca'

            ).add_to(m)
            m.save('templates\location.html')
            return render_template('device_info.html', temp=f_temp, hum=f_hum, name=name, company=key, city=city , Over = Over)
        except:

            return redirect(url_for('device'))
    return redirect(url_for("login"))


@app.route('/weather', methods=['GET', 'POST'])
def weather():
    if "key" in session:

        try:
            key = session["key"]
            code_ = session["code_selected"]
            print(code_)
            url_device = ('https://api.thingspeak.com/channels/' + code_ + '/feeds.json?results=2')
            req = requests.get(url_device)
            json_file = req.json()['feeds']
            print(json_file)
            x = (loads(req.text)['feeds'])
            y = x[0]
            longitude = y['field3']
            latitude = y['field4']
            long = 36.79800033569336
            att = 10.171699523925781
            url_weather = requests.get(
                'http://api.openweathermap.org/data/2.5/weather?lat=' + str(long) + '&lon=' + str(
                    att) + '&appid=0c2b40ce81103e261f0b56bc85b40dff')
            json_object = url_weather.json()
            print(json_object)
            temp_k = float(json_object['main']['temp'])
            temp_c = "%.2f" % (temp_k - 273.15)
            wind_speed = float(json_object['wind']['speed'])
            city_ = str(json_object['name'])
            country_ = str(json_object['sys']['country'])
            return render_template('weather.html', temp=temp_c, wind=wind_speed, country=country_, city=city_)
        except:
            return redirect(url_for('device'))
    return redirect(url_for("login"))


@app.route('/location', methods=['GET', 'POST'])
def location():
    if "key" in session:
        key = session["key"]
        return render_template('location.html')
    return redirect(url_for("login"))


@app.route('/mission', methods=['GET', 'POST'])
def mission():
    global unsuccessful, successful
    if "key" in session:
        key = session["key"]
        if request.method == 'POST':
            worker = request.form['worker']
            mission_ = request.form['mission']
            company = request.form['Company']
            vehicle = request.form['Vehicle']
            phone = request.form['Phone']
            created = datetime.utcnow()
            try:
                if worker and mission_ and phone and vehicle and company:
                    db.child(company).child("_worker").set(worker)
                    db.child(company).child("mission").set(mission_)
                    db.child(company).child("company").set(company)
                    db.child(company).child("vehicle").set(vehicle)
                    db.child(company).child("phone").set(phone)
                    db.child(company).child("date").set(str(created))
                    successful = 'Mission Added'
                return render_template('mission.html', smessage=successful)
            except:
                worker = not worker
                unsuccessful = 'Fill up the mission'
                render_template('mission.html', umessage=unsuccessful)

        return render_template('mission.html')
    return redirect(url_for("login"))


@app.route('/mission_exist', methods=['GET', 'POST'])
def mission_exist():
    if "key" in session:
        try:
            key = session["key"]
            worker = db.child(key).child('_worker').get().val()
            phone = db.child(key).child("phone").get().val()
            mission = db.child(key).child("mission").get().val()
            company = db.child(key).child("company").get().val()
            vehicle = db.child(key).child("vehicle").get().val()
            date = db.child(key).child("date").get().val()

            return render_template('mission_exist.html', worker=worker, mission=mission, phone=phone, company=company,
                                   vehicle=vehicle, date=date)
        except:
            return redirect(url_for('mission'))
    return redirect(url_for("login"))


@app.route('/delete_mission')
def delete_mission():
    if "key" in session:
        try:
            key = session["key"]
            worker = db.child(key).child('_worker').remove()
            phone = db.child(key).child("phone").remove()
            mission = db.child(key).child("mission").remove()
            company = db.child(key).child("company").remove()
            vehicle = db.child(key).child("vehicle").remove()
            date = db.child(key).child("date").get().remove()

            return redirect(url_for('mission'))
        except:
            return redirect(url_for('mission_exist'))
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("key", None)
    return redirect(url_for("login"))


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        email_ = request.form['email_']
        password_ = request.form['password_']
        secret = request.form['secret']
        session["secret"] = secret
        if secret == "azibra1595":
            try:

                auth.sign_in_with_email_and_password(email_, password_)
                # session['usr'] = user_id
                # user_id = auth.get_account_info(user['idToken'])
                return redirect(url_for('add_device'))
            except:
                unsuccessful = 'Please check your credentials'
                return render_template("admin.html", umessage=unsuccessful)
        unsuccessful = 'Wrong secret '
        return render_template("admin.html", umessage=unsuccessful)
    return render_template('admin.html')


@app.route('/logout_admin')
def logout_admin():
    session.pop('secret', None)
    return redirect(url_for("admin"))


@app.route('/add_device', methods=['GET', 'POST'])
def add_device():
    if "secret" in session:
        if request.method == 'POST':
            device_ = request.form['Device']
            company = request.form['Company']
            name = request.form['name']

            db.child(company).child("Devices").child(name).set(name)
            db.child(company).child("Devices").child(name).set(device_)

            return render_template('add_device.html')

        return render_template('add_device.html')
    return redirect(url_for("admin"))


if __name__ == '__main__':
    app.run()

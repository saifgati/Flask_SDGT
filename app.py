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
    if "key" in session:
        return render_template("home_index.html")
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        key = request.form['Key']

        try:
            session["key"] = key
            radio_b = request.form['radio']
            user = auth.sign_in_with_email_and_password(email, password)
            user_id = auth.get_account_info(user['idToken'])

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
            user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(user['idToken'])
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
    global temp_k, hum_p, Over, f_temp, f_hum, long, att, speed_
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
                long = longitude
                att = latitude
                speed = y['field5']
                speed_ = "%.1f" % float(speed)
                time.sleep(3)
            m = folium.Map(location=[long, att], zoom_start=12)
            tooltip: str = "Click for more info"
            folium.Marker([long, att],
                          popup=f'<strong>Speed: {speed_} ID:{code}</strong>',
                          tooltip=tooltip
                          , icon=folium.Icon(color='black', icon='cloud')).add_to(m)
            folium.CircleMarker(
                location=(long, att),
                radius=30,
                popup='Location',
                color='#428bca',
                fill=True,
                fill_color='#428bca'

            ).add_to(m)
            '''route_lats_longs = [[34.041008, -118.246653],
                                [36.169726, -115.143996],
                                [39.739448, -104.992450],
                                [41.878765, -87.643267],
                                [40.782949, -73.969559]]

            # add route to map
            folium.PolyLine(route_lats_longs).add_to(m)'''
            m.save('templates\location.html')
            return render_template('device_info.html', temp=f_temp, hum=f_hum, speed=speed_, name=name, company=key,
                                   city=city, Over=Over)
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
            long = longitude
            att = latitude
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
        try:
            key = session["key"]
            return render_template('location.html')
        except:
            return redirect(url_for("device_info"))
    return redirect(url_for("login"))


@app.route('/mission', methods=['GET', 'POST'])
def mission():
    global unsuccessful, successful
    if "key" in session:
        key = session["key"]
        if request.method == 'POST':
            worker = request.form['worker']
            mission_ = request.form['mission']
            vehicle = request.form['Vehicle']
            Destination = request.form['Destination']
            phone = request.form['Phone']
            created = datetime.utcnow()
            worker = str(worker).upper()

            try:
                if worker and mission_ and phone and vehicle:
                    db.child(key).child("Missions").child(worker).child("_worker").set(worker)
                    db.child(key).child("Missions").child(worker).child("mission").set(mission_)
                    db.child(key).child("Missions").child(worker).child("vehicle").set(vehicle)
                    db.child(key).child("Missions").child(worker).child("Destination").set(Destination)
                    db.child(key).child("Missions").child(worker).child("phone").set(phone)
                    db.child(key).child("Missions").child(worker).child("date").set(str(created))
                    successful = 'Mission Added'
                    session["mission"] = worker



                return render_template('mission.html', smessage=successful)
            except:

                unsuccessful = 'Fill up the mission'
                return render_template('mission.html', umessage=unsuccessful)

        return render_template('mission.html')
    return redirect(url_for("login"))


@app.route('/delete_mission_from_all', methods=['GET', 'POST'])
def delete_mission_from_all():
    if "key" in session:
        key = session["key"]
        mission_by_selection_ = db.child(key).child("Missions").get()
        return render_template('delete_mission_from_all.html', mission_by_selection_= mission_by_selection_)
    return redirect(url_for("login"))
@app.route('/delete_mission_from_all_selected', methods=['GET', 'POST'])
def delete_mission_from_all_selected():
    if "key" in session:
        key = session["key"]
        mission_to_delete = request.form.get('mission_to_delete')
        mission_to_delete = mission_to_delete[:]
        print(mission_to_delete)
        db.child(key).child("Missions").child(mission_to_delete).remove()
        return redirect(url_for("mission_by_selection"))
    return redirect(url_for("login"))

@app.route('/mission_by_selection', methods=['GET', 'POST'])
def mission_by_selection():
    if "key" in session:
        key = session["key"]
        mission_by_selection_ = db.child(key).child("Missions").get()
        return render_template('mission_by_selection.html', mission_by_selection_= mission_by_selection_)
    return redirect(url_for("login"))

@app.route('/mission_exist', methods=['GET', 'POST'])#last mission
def mission_exist():
    if "key" in session:
        if "mission" in session:
            worker = session["mission"]
            try:
                key = session["key"]

                worker = db.child(key).child("Missions").child(worker).child('_worker').get().val()
                phone = db.child(key).child("Missions").child(worker).child("phone").get().val()
                mission = db.child(key).child("Missions").child(worker).child("mission").get().val()
                vehicle = db.child(key).child("Missions").child(worker).child("vehicle").get().val()
                destination = db.child(key).child("Missions").child(worker).child("Destination").get().val()
                date = db.child(key).child("Missions").child(worker).child("date").get().val()

                return render_template('mission_exist.html', worker=worker, mission=mission, phone=phone,
                                       vehicle=vehicle, date=date , destination = destination)
            except:
                return redirect(url_for('mission'))
        return redirect(url_for('mission'))
    return redirect(url_for("login"))


@app.route('/delete_mission')
def delete_mission():
    if "key" in session:
        if "mission" in session:
            worker = session["mission"]
            try:
                key = session["key"]
                worker_ = db.child(key).child("Missions").child(worker).remove()
                #phone = db.child(key).child("Missions").child(worker).child("phone").remove()
                #mission = db.child(key).child("Missions").child(worker).child("mission").remove()
                #vehicle = db.child(key).child("Missions").child(worker).child("vehicle").remove()
                #vehicle = db.child(key).child("Missions").child(worker).child("Destination").remove()

                session.pop("mission", None)
                return redirect(url_for('mission'))
            except:
                return redirect(url_for('mission_exist'))
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
                return redirect(url_for('admin_home'))
            except:
                unsuccessful = 'Please check your credentials'
                return render_template("admin.html", umessage=unsuccessful)
        unsuccessful = 'Wrong secret '
        return render_template("admin.html", umessage=unsuccessful)
    return render_template('admin.html')


@app.route('/admin_home', methods=['GET', 'POST'])
def admin_home():
    return render_template('admin_home.html')


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
            smessage = 'Device Added'

            return render_template('add_device.html', smessage=smessage)

        return render_template('add_device.html')
    return redirect(url_for("admin"))

@app.route('/add_company', methods=['GET', 'POST'])
def add_company():
    if "secret" in session:
        if request.method == 'POST':
            company = request.form['Company']
            company_id = request.form['company_id']

            db.set(company)
            db.child(company).set(company_id)
            smessage = 'Company Added'

            return render_template('add_company.html', smessage=smessage)

        return render_template('add_company.html')
    return render_template('admin.html')
@app.route('/add_worker', methods=['GET', 'POST'])
def add_worker():
    if "secret" in session:
        if request.method == 'POST':
            company = request.form['Company']
            Worker_name = request.form['Worker_name']
            db.child(company).set(Worker_name)
            smessage = 'Worker Added'

            return render_template('add_worker.html', smessage=smessage)

        return render_template('add_worker.html')
    return render_template('admin.html')
@app.route('/delete_device', methods=['GET', 'POST'])
def delete_device():
    if "secret" in session:
        if request.method == 'POST':
            device_ = request.form['Device']
            company = request.form['Company']
            name = request.form['name']

            db.child(company).child("Devices").child(name).remove(name)
            db.child(company).child("Devices").child(name).remove(device_)
            smessage = "Deleted"

            return render_template('add_device.html', smessage=smessage)

        return render_template('add_device.html')
    return redirect(url_for("admin"))


@app.route('/shipments', methods=['GET', 'POST'])
def shipments():
    return render_template('shipments.html')


@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    return render_template('inventory.html')


@app.route('/field_assets', methods=['GET', 'POST'])
def field_assets():
    return render_template('field_assets.html')


@app.route('/multimodel_shipment_tracking', methods=['GET', 'POST'])
def multimodel_shipment_tracking():
    return render_template('multimodel_shipment_tracking.html')


@app.route('/pharma_cold', methods=['GET', 'POST'])
def pharma_cold():
    return render_template('pharma_cold.html')


@app.route('/spoilage_monitoring', methods=['GET', 'POST'])
def spoilage_monitoring():
    return render_template('spoilage_monitoring.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if "key" in session:

        try:
            edit_profile()
            key = session["key"]
            name = db.child(key).child('name').get().val()
            phone = db.child(key).child("phone").get().val()
            company = db.child(key).child("company").get().val()
            city = db.child(key).child("city").get().val()
            return render_template('profile.html', name=name, phone=phone, company=company, city=city)
        except:
            return redirect(url_for('index'))

    return redirect(url_for("login"))


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if request.method == 'POST':
        if "key" in session:
            company = request.form['company']
            phone = request.form['phone']
            name = request.form['name']
            city = request.form['city']

            try:
                key = session["key"]
                db.child(key).child('name').set(name)
                db.child(key).child("phone").set(phone)
                db.child(key).child("company").set(company)
                db.child(key).child("city").set(city)
                return render_template("profile.html")
            except:
                return render_template('profile.html')

        return redirect(url_for("login"))
    return render_template("edit_profile.html")


if __name__ == '__main__':
    app.run()

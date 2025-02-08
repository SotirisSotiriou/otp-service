from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
import random
import datetime
from dotenv import load_dotenv
import os

# For email send OTP
import smtplib
from email.mime.text import MIMEText

# For SMS send OTP
from twilio.rest import Client

# Check if running on local environment
if os.path.exists('.env'):
    ENV = 'local'
else:
    ENV = 'production'

# Load environment variables
if ENV == 'local':
    load_dotenv()

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

# Email Configuration
app.config['EMAIL_HOST'] = os.getenv('EMAIL_HOST')
app.config['EMAIL_PORT'] = int(os.getenv('EMAIL_PORT'))  # Convert to int
app.config['EMAIL_USERNAME'] = os.getenv('EMAIL_USERNAME')
app.config['EMAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')

# Twilio Configuration
app.config['TWILIO_ACCOUNT_SID'] = os.getenv('TWILIO_ACCOUNT_SID')
app.config['TWILIO_AUTH_TOKEN'] = os.getenv('TWILIO_AUTH_TOKEN')
app.config['TWILIO_PHONE_NUMBER'] = os.getenv('TWILIO_PHONE_NUMBER')

mysql = MySQL(app)

def generate_otp():
    return str(random.randint(100000, 999999))

def send_email(to_email, otp):
    subject = "Your OTP Code"
    body = f"Your one-time password (OTP) is: {otp}"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = app.config['EMAIL_USERNAME']
    msg['To'] = to_email

    with smtplib.SMTP(app.config['EMAIL_HOST'], app.config['EMAIL_PORT']) as server:
        server.starttls()
        server.login(app.config['EMAIL_USERNAME'], app.config['EMAIL_PASSWORD'])
        server.send_message(msg)

def send_sms(to_phone, otp):
    client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])

    message = client.messages.create(
        body=f"Your one-time password (OTP) is: {otp}",
        from_=app.config['TWILIO_PHONE_NUMBER'],
        to=to_phone
    )



@app.route('/generate_otp', methods=['POST'])
def generate_otp_route():
    data = request.get_json()
    user_id = data.get('user_id')
    otp = generate_otp()
    expires_at = datetime.datetime.now() + datetime.timedelta(minutes=2)  # OTP valid for 2 minutes

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO otps (user_id, otp, expires_at) VALUES (%s, %s, %s)", (user_id, otp, expires_at))
    mysql.connection.commit()
    cur.close()

    # # Fetch user information from the database
    # cur = mysql.connection.cursor()
    # cur.execute("SELECT email, phone FROM users WHERE id = %s", (user_id,))
    # user_info = cur.fetchone()
    # cur.close()

    # if not user_info:
    #     return jsonify({'message': 'User  not found.'}), 404

    # email, phone = user_info


    # # Send OTP via email and/or SMS if defined
    # if email:
    #     send_email(email, otp)
    # if phone:
    #     send_sms(phone, otp)

    # return jsonify({'message': 'OTP sent via email and/or SMS.'}), 201

    return jsonify({'otp': otp, 'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')}), 201

@app.route('/validate_otp', methods=['POST'])
def validate_otp_route():
    data = request.get_json()
    user_id = data.get('user_id')
    otp = data.get('otp')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM otps WHERE user_id = %s AND otp = %s AND expires_at >= NOW()", (user_id, otp))
    result = cur.fetchone()
    cur.close()

    if result:
        # OTP is valid, delete it from the database
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM otps WHERE user_id = %s AND otp = %s", (user_id, otp))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'OTP is valid.'}), 200
    else:
        return jsonify({'message': 'OTP is invalid or expired.'}), 400

if __name__ == '__main__':
    app.run(debug=True)
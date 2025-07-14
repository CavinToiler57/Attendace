from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import pandas as pd
import smtplib
from email.message import EmailMessage
import csv
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Database Model
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    action = db.Column(db.String(10))  # checkin / checkout
    timestamp = db.Column(db.DateTime, default=datetime.now)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    action = request.form['action'].lower()
    time_now = datetime.now().strftime('%Y-%m-%d %I:%M %p')
    today = date.today()

    # Check if already did the same action today
    existing = Attendance.query.filter_by(email=email, action=action.capitalize()).all()
    for entry in existing:
        if entry.timestamp.date() == today:
            message = f"You already did a {action.capitalize()} today!"
            return render_template('thank_you.html', message=message)

    # Save to database
    new_entry = Attendance(name=name, email=email, action=action.capitalize())
    db.session.add(new_entry)
    db.session.commit()

    # Save to CSV log file
    with open('attendance_log.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([name, email, action.capitalize(), time_now])

    message = f"{action.capitalize()} recorded successfully for {name} at {time_now}."
    return render_template('thank_you.html', message=message)

    # Save to CSV log file
    with open('attendance_log.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([name, email, action.capitalize(), time_now])

    message = f"{action.capitalize()} recorded successfully for {name} at {time_now}."
    return render_template('thank_you.html', message=message)

@app.route('/export')
def export():
    export_attendance()
    return "CSV exported as attendance_report.csv"

@app.route('/send_email')
def send_email():
    export_attendance()
    send_report_to_hr()
    return "Email sent to HR with report!"

# Export function
def export_attendance():
    records = Attendance.query.all()
    data = [{
        "Name": r.name,
        "Email": r.email,
        "Action": r.action,
        "Time": r.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for r in records]

    df = pd.DataFrame(data)
    df.to_csv("attendance_report.csv", index=False)

# Email function
def send_report_to_hr():
    msg = EmailMessage()
    msg['Subject'] = 'Daily Attendance Report'
    msg['From'] = 'youremail@gmail.com'
    msg['To'] = 'hr@yourcompany.com'
    msg.set_content('Please find attached today’s attendance report.')

    with open('attendance_report.csv', 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='csv', filename='attendance_report.csv')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('youremail@gmail.com', 'your_app_password')  # Use Gmail App Password
        smtp.send_message(msg)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

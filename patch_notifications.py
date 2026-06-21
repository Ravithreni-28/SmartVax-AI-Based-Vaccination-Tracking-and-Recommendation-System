import os

path = 'app.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
found = False
for line in lines:
    if 'send_vaccine_reminder_email(app, user.id, reminder.id)' in line and not found:
        new_lines.append('                # IN-APP NOTIFICATION ENGINE\n')
        new_lines.append('                notif_t = f"Due: {reminder.vaccine.vaccine_name}"\n')
        new_lines.append('                if not Notification.query.filter_by(user_id=user.id, is_read=False, title=notif_t).first():\n')
        new_lines.append('                    db.session.add(Notification(user_id=user.id, title=notif_t, message=f"Vaccine {reminder.vaccine.vaccine_name} is due.", type="warning"))\n')
        new_lines.append('                    db.session.commit()\n\n')
        found = True
    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('SUCCESS')

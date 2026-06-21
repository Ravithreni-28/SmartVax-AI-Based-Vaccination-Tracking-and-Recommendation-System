import os
from datetime import date, datetime

path = 'app.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
found_scan = False
for line in lines:
    new_lines.append(line)
    if 'def check_and_send_reminders():' in line and not found_scan:
        new_lines.append('    # MASTER SYNC FOR ALL OVERDUE VACCINES\n')
        new_lines.append('    with app.app_context():\n')
        new_lines.append('        from models.models import User, UserVaccine, Notification\n')
        new_lines.append('        users = User.query.all()\n')
        new_lines.append('        for u in users:\n')
        new_lines.append('            age_m = u.get_age_in_months()\n')
        new_lines.append('            overdue = UserVaccine.query.filter_by(user_id=u.id, status="Pending").all()\n')
        new_lines.append('            for uv in overdue:\n')
        new_lines.append('                if uv.vaccine.recommended_age_months <= age_m:\n')
        new_lines.append('                    t = f"Overdue: {uv.vaccine.vaccine_name}"\n')
        new_lines.append('                    if not Notification.query.filter_by(user_id=u.id, is_read=False, title=t).first():\n')
        new_lines.append('                        db.session.add(Notification(user_id=u.id, title=t, message=f"{uv.vaccine.vaccine_name} is overdue.", type="danger"))\n')
        new_lines.append('        db.session.commit()\n')
        found_scan = True

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('SUCCESS')

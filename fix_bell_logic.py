import os

path = 'app.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Target the unread_count line in get_notifications route
old_code = "unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()"
new_code = """from models.models import Reminder
    unread_count = Reminder.query.filter_by(user_id=current_user.id, is_active=True).count()"""

if old_code in text:
    text = text.replace(old_code, new_code)
    # Also clean up the 'Overdue' title in previous patch
    text = text.replace('Overdue: ', 'Due: ')
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('SUCCESS')
else:
    print('COULD NOT FIND STARTING LOGIC')

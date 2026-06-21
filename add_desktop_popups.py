import os

path = 'templates/base.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_line = "badge.innerText = data.unread_count; badge.classList.remove('d-none');"
replacement = (
    "if (window._lastCount !== undefined && data.unread_count > window._lastCount && Notification.permission === 'granted') {\n"
    "              new Notification('SmartVax Reminder', { body: 'You have vaccine tasks to check!', icon: '/static/img/icon-192.png' });\n"
    "            }\n"
    "            window._lastCount = data.unread_count;\n"
    "            badge.innerText = data.unread_count; badge.classList.remove('d-none');"
)

if old_line in text:
    text = text.replace(old_line, replacement)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('SUCCESS')
else:
    print('NOT FOUND')

import os

path = 'templates/base.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Add permission request to the bell icon anchor tag
old_anchor = 'id=\"notifDropdown\" data-bs-toggle=\"dropdown\"'
new_anchor = 'id=\"notifDropdown\" data-bs-toggle=\"dropdown\" onclick=\"if(Notification.permission===\'default\') Notification.requestPermission();\"'

if old_anchor in text:
    text = text.replace(old_anchor, new_anchor)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('SUCCESS')
else:
    # Try alternate match if ID was missing
    text = text.replace('href=\"#\" data-bs-toggle=\"dropdown\"', 'href=\"#\" data-bs-toggle=\"dropdown\" onclick=\"if(Notification.permission===\'default\') Notification.requestPermission();\"')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('SUCCESS (Alt match)')

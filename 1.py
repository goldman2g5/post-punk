hui = "huii"

html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Чат 3</title>
</head>
<body>

<script>
    let ws = new WebSocket("ws://127.0.0.1:8010/ws/server");
    ws.onopen = function () {{
        let message = {{message: {hui}, user: "server"}}
        let messageJson = JSON.stringify(message);
        ws.send(messageJson);
    }}
</script>
</body>
</html>
"""

print(html_content)
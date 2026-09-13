import json, os, urllib.request

def handler(request):
    if request.method != 'POST':
        return {'statusCode': 405, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': 'POST required'})}
    key = os.environ.get('GROQ_API_KEY')
    if not key:
        return {'statusCode': 503, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': 'GROQ_API_KEY is not configured on Vercel'})}
    try:
        body = request.get_json() if hasattr(request, 'get_json') else json.loads(request.body)
        messages = body.get('messages', [])
        payload = json.dumps({'model': os.environ.get('AI_MODEL', 'llama-3.3-70b-versatile'), 'messages': messages, 'temperature': float(os.environ.get('AI_TEMPERATURE', '0.7'))}).encode()
        req = urllib.request.Request('https://api.groq.com/openai/v1/chat/completions', data=payload, headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=30) as r: data = json.loads(r.read())
        return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'message': data['choices'][0]['message']})}
    except Exception as e:
        return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': str(e)})}
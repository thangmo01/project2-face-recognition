from flask import Response
import json

def goResponse(code: int, status: int, result: dict, messages: str = ''):
    return Response(
        response=json.dumps({
            "code": code,
            "messages": messages,
            "result": result
        }),
        status=status,
        mimetype='application/json'
    )
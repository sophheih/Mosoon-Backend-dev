from django.http import HttpResponse
from rest_framework.decorators import api_view


@api_view(['GET'])
def get_system_status(request):
    response_html = """
    <html>
        <body style="display: flex; align-items: center; justify-content: center;">
            <div style="text-align: center; font-family: 'Noto Sans TC', '微軟正黑體', sans-serif;">
                <h1>This is the backend server of Mosoon Massage Manage System.</h1>
                <p>If you see this message, the API service is connect from your client successfully.</p>
            </div>
        </body>
    <html>
    """
    return HttpResponse(response_html)

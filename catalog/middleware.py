

class PathLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response # einmalig

    def __call__(self, request):
        print(f"[Middleware] eingehend: {request.path}")
        response = self.get_response(request) # Das Aufrufen von der nächsten Middleware-Schicht oder View 
        print(f"[Middleware] Status: {response.status_code}")
        return response

    
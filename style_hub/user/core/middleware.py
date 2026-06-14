from django.contrib.messages import get_messages

class ClearMessagesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Clear/consume messages only on a successful HTML response (200 OK)
        # to prevent them from leaking into other pages, while preserving
        # them for redirects (302) or failures.
        if response.status_code == 200:
            storage = get_messages(request)
            for _ in storage:
                pass
        return response

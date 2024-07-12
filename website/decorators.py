# decorators.py

from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('signin')  # or the URL name of your login page
        return view_func(request, *args, **kwargs)
    return wrapper
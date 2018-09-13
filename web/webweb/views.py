from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth import logout,authenticate, login
from django.contrib.auth.models import User


# Create your views here.
def index(request, error=''):
    return render_to_response("index.html", {'logged_in': request.user.is_authenticated, 'error':error})


def user_logout(request):
    logout(request)
    return index(request)


def user_login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    error = ''
    if user is not None:
        login(request, user)
    else:
        error = '用户名/密码错误'
    return index(request, error=error)


def user_register(request):
    username = request.POST['username']
    password = request.POST['password']
    ans = User.objects.filter(username=username)
    if len(ans):
        return index(request, error="用户已存在")
    user = User.objects.create_user(username, email=None, password=password)
    user = authenticate(request, username=username, password=password)
    login(request, user)
    return index(request)
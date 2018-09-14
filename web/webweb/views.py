from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.contrib.auth import logout,authenticate, login
from django.contrib.auth.models import User
import redis
import redis_lock
r = redis.StrictRedis(host='localhost', port=6379, db=0)
# the first image fetch is slow, so we put it here
with redis_lock.Lock(r, "image"):
    img = r.get('image')


# Create your views here.
def index(request):
    error = "" if 'error' not in request.session else request.session['error']
    if 'error' in request.session:
        del request.session['error']
    return render_to_response("index.html", {'logged_in': request.user.is_authenticated, 'error':error})


def user_logout(request):
    logout(request)
    request.session['error'] = ""
    return HttpResponseRedirect("/")


def user_login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    error = ''
    if user is not None:
        login(request, user)
    else:
        error = '用户名/密码错误'
    request.session['error'] = error
    return HttpResponseRedirect("/")


def user_register(request):
    username = request.POST['username']
    password = request.POST['password']
    ans = User.objects.filter(username=username)
    if len(ans):
        error = "用户已存在"
        request.session['error'] = error
        return HttpResponseRedirect("/")
    user = User.objects.create_user(username, email=None, password=password)
    user = authenticate(request, username=username, password=password)
    login(request, user)
    request.session['error'] = error
    return HttpResponseRedirect("/")
    
    
def user_reset(request):
    username = request.POST['username']
    old = request.POST['old']
    new = request.POST['new']
    user = authenticate(request, username=username, password=old)
    error = ''
    if user is not None:
        # user.password = new
        user.set_password(new)
        user.save()
        error = "修改成功"
    else:
        error = '用户名/密码错误'
    request.session['error'] = error
    return HttpResponseRedirect("/")
    
    
    
def my_image(request):
    print('img!')
    img = None
    with redis_lock.Lock(r, "image"):
        img = r.get('image')
    return HttpResponse(img, content_type="image/jpg")
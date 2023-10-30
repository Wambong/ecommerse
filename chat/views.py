from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
# Create your views here.
from chat.models import Thread


def login(request):
    if request.method=='POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username= username, password= password)

        if user is not None:
            auth.login(request,user)
            return redirect('/')
        else:
            messages.error(request,'Username/Password is incorrect')
            return redirect('login')
    else:
        return render(request,"login.html")


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if password1==password2:
            if User.objects.filter(username=username).exists():
                messages.info(request,'username already exist')
            elif User.objects.filter(email=email).exists():
                messages.info(request,'email already exist')
            else:
                user = User.objects.create_user(username = username, first_name= first_name, last_name= last_name, email=email,password=password1)
                user.save()
                messages.info(request,'User created')
                return redirect('login')
        else:
            messages.info(request, 'Password not match')
        return redirect('register')
    else:
        return render(request,"register.html")

def logout(request):
    auth.logout(request)
    return redirect('/')

def profile(request):
    u = request.user
    if request.method == 'POST':
        username = request.POST['username']
        first_name = request.POST['fn']
        last_name = request.POST['ln']
        email = request.POST['email']
        old = request.POST['old']
        new = request.POST['new']
        user = User.objects.get(pk = u.pk)
        if User.objects.filter(username=username).exclude(pk=u.pk).exists():
            messages.error(request,'Username already exists')
        elif User.objects.filter(email=email).exclude(pk=u.pk).exists():
                messages.error(request,'Email already exists')
        elif user.check_password(old):
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.set_password(new)
            user.save()
            #update session
            update_session_auth_hash(request, user)
            messages.success(request,'Profile updated')
        else:
            messages.error(request,'Wrong Old Password')
        return redirect('profile')
    else:
        user = request.user
        return render(request,"profile.html")

from django.http import Http404

@login_required
def create_thread(request, username):
    try:
        other_user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404("User not found")  # Handle the case where the user doesn't exist

    thread = Thread.objects.by_user(user=request.user).filter(
        Q(first_person=other_user) | Q(second_person=other_user)
    ).first()

    if thread is None:
        thread = Thread.objects.create(first_person=request.user, second_person=other_user)

    return redirect('view_thread', thread_id=thread.id)

@login_required
def messages_page(request):
    threads = Thread.objects.by_user(user=request.user).prefetch_related('chatmessage_thread').order_by('timestamp')

    context = {
        'Threads': threads,
    }
    return render(request, 'messages.html', context)






from django.shortcuts import render, get_object_or_404
from .models import Thread

def view_thread(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    messages = thread.chatmessage_thread.all()

    context = {
        'thread': thread,
        'messages': messages,
    }

    return redirect("chat")

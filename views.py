from django.shortcuts import render, redirect
from .models import Room, Topic, Message, Likes
from .forms import RoomForm, UserForm
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:  # User can't access login page if already logged in
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()  # Gets the username we typed in and password
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)  # Checks to see if username in database or if doesnt exist

        except User.DoesNotExist:
            messages.error(request, 'Username does not exist')

        user = authenticate(request, username=username, password=password)  # Authenticates the credentials taking in username and password as arguments
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username or Password does not exist')

    context = {'page': page}
    return render(request, 'Login_signup.html', context=context)


def logoutuser(request):
    logout(request=request)
    return redirect('home')


def registerpage(request):
    form = UserCreationForm()
    context = {'form': form}

    if request.method == 'POST':
        form = UserCreationForm(request.POST) # Passes in the credentials we sent such as username password
        if form.is_valid():
            user = form.save(commit=False)  # Setting to false returns the object and doesnt save it to database yet so we can edit it
            user.username = user.username.lower()
            user.save()
            login(request, user=user)
            return redirect('home')
        else:
            messages.error(request, 'Passwords require 8 letters/That Username may be taken')

    return render(request, 'Login_signup.html', context=context)


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''  # Makes it so you can type after ?q= and page pops up
    # All tag on front page is result of q == None, hence all activity shows on right as well
    rooms = Room.objects.filter(Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q) | Q(host__username__icontains=q))  # Icontains makes it case insensitive as opposed to just contains
    total_rooms = Room.objects.filter()
    room_count = total_rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q) | Q(room__name__icontains=q))[0:5]
    topics = Topic.objects.all()[0:5]  # Grabs all attributes from Topics class

    page = request.GET.get('page', 1)

    paginator = Paginator(rooms, 6)
    try:
        rooms = paginator.page(page)
    except PageNotAnInteger:
        rooms = paginator.page(1)
    except EmptyPage:
        rooms = paginator.page(paginator.num_pages)

    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count,
               'room_messages': room_messages}
    return render(request, 'Home.html', context=context)  # Context is basically a dictionary mapping variable names
    #  to values which are passed onto templates through render


def room(requests, primarykey):
    room = Room.objects.get(id=primarykey) # Makes it so rooms are labeled ex: /room/1
    room_messages = room.message_set.all()  # Gives us all the Message objects from the models.py file for each room as indicated by line above
    participants = room.participants.all()
    likes = room.likes_set.all().count()
    if requests.method == 'POST':
        if requests.user.is_authenticated and 'body' in requests.POST: # Grabs the name of the input in our room.html file and makes sure it 'body'
            room_messages = Message.objects.create(user=requests.user, room=room, body=requests.POST.get('body'))  # Create
            # these values by referencing the Message class from models.py
            room.participants.add(requests.user)
            return redirect('room', primarykey=room.id)

        elif requests.user.is_authenticated and 'like' in requests.POST:
            if Likes.objects.filter(user=requests.user, room=room).exists():
                messages.error(requests, 'You have already liked this post')
            else:
                like = Likes.objects.create(user=requests.user, room=room)
                room.participants.add(requests.user)
                return redirect('room', primarykey=room.id)

        else:
            return redirect('login')

    context = {'room': room, 'room_messages': room_messages, 'participants': participants,
               'likes': likes}
    return render(requests, 'Room.html', context)


@login_required(login_url='login')
@staff_member_required(login_url='home')
def createRoom(request):
    form = RoomForm()  # Taken from forms.py and will load the foreignkeys from Room class: host and topic, as well
    # as textfields: name and description
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)  # Either get the topic from Topics model or
        # create a new topic and add it to the model/database.
        Room.objects.create(host=request.user,
                            topic=topic,
                            name=request.POST.get('name'),
                            description=request.POST.get('description')
                            )

        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'room_form.html', context=context)


@login_required(login_url='login')
@staff_member_required(login_url='home')
def updateRoom(request, primarykey):
    room = Room.objects.get(id=primarykey)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('You are not the owner of this room')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'room_form.html', context=context)


@login_required(login_url='login')
@staff_member_required(login_url='login')
def deleteRoom(request, primarykey):
    room = Room.objects.get(id=primarykey)  # Returns the str method which is just self.name of the room

    if request.user != room.host:
        return HttpResponse('You are not the owner of this room')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'Delete.html', context={'obj': room})


@login_required(login_url='login')
def deleteMessage(request, primarykey):
    message = Message.objects.get(id=primarykey)  # Returns self.body from str method which is text

    if not request.user.is_superuser:
        if request.user != message.user:
            return HttpResponse('You are not the owner of this room')

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'Delete.html', context={'obj': message})


def userprofile(request, primarykey):
    user = User.objects.get(id=primarykey)
    rooms = user.room_set.all()
    liked_rooms = user.likes_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()

    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics,
               'liked_rooms': liked_rooms}

    return render(request, 'profile.html', context=context)


@login_required(login_url='login')
def updateuser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', primarykey=user.id)

    context = {'form': form, 'user': user}
    return render(request, 'update-user.html', context=context)


def topicspage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics': topics}
    return render(request, 'topics.html', context=context)


@staff_member_required(login_url='home')
def activities(request):
    room_messages = Message.objects.all()[0:2]
    context = {'room_messages': room_messages}
    return render(request, 'activity.html', context=context)




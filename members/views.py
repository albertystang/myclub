from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import SignUpForm


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'You have logged in successfully...')
            return redirect('home')
        else:
            messages.success(request, 'There is an error in logging in. Please try again...')
    return render(request, 'authenticate/login.html')


def logout_user(request):
    logout(request)
    messages.success(request, 'You have logged out successfully...')
    return redirect('home')


def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = request.POST['username']
            password = request.POST['password1']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'You have created an account successfully...')
                return redirect('home')
        else:
            messages.success(request, 'There is an error in signing up. Please try again...')
    form = SignUpForm()
    context = {'form': form}
    return render(request, 'authenticate/register.html', context)             
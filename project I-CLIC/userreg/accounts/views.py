from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import LoginForm
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect
from .models import Prediction
from django import forms
from django.contrib.auth.decorators import login_required


def landing_page(request):
    return render(request, 'accounts/tampilandepan.html')


def templatechatbot(request):
    return render(request, 'accounts/templatechatbot.html')


def riwayat_view(request):
    return render(request, 'accounts/riwayat.html')  


def artikel_view(request):
    # gunakan model Prediction, bukan variabel predictions
    predictions = Prediction.objects.all()
    return render(request, 'accounts/artikel.html', {'predictions': predictions})


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])  # Hash password
            user.save()
            return redirect('register_success')  # Redirect ke halaman sukses
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})  # Tambahkan return statement untuk GET request

def register_success(request):
    return render(request, 'accounts/register_succes.html')


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            uname = form.cleaned_data['username']
            pwd = form.cleaned_data['password']
            user = authenticate(request, username=uname, password=pwd)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # ganti sesuai kebutuhanmu
            else:
                form.add_error(None, 'Username atau password salah')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')
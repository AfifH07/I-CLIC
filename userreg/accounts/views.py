from django.shortcuts import render, redirect
from .forms import UserRegistrationForm, LoginForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from .models import Prediction


def landing_page(request):
    return render(request, 'accounts/tampilandepan.html')

def logout_view(request):
    logout(request)
    return redirect('tampilandepan')

@login_required
def templatechatbot(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        user_email = request.user.email  # Ambil email user yang login
        prediction = Prediction.objects.filter(user_id=user_id).order_by('-predicted_at').first()
        if prediction:
            prediction_name = prediction.prediction_name
        else:
            prediction_name = None
    else:
        prediction_name = None
        user_email = None

    context = {
        'prediction_name': prediction_name,
        'user_email': user_email,
    }

    return render(request, 'accounts/templatechatbot.html', context)


def riwayat_view(request):
    return render(request, 'accounts/riwayat.html')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Prediction, Article

keyword_map = {
    'Healthy': 1,
    'Bronchitis': 2,
    'Flu': 3,
    'Cold': 4,
    'Pneumonia': 5
}

@login_required
def artikel_view(request):
    user = request.user
    prediction_name = None
    articles = []

    # Ambil prediksi terbaru user
    prediction = Prediction.objects.filter(user=user).order_by('-predicted_at').first()
    if prediction:
        prediction_name = prediction.prediction_name
        
        # Encode prediction_name ke prediction_idU
        prediction_idU = keyword_map.get(prediction_name, None)
        
        if prediction_idU:
            # Query 6 artikel terbaru berdasarkan prediction_idU
            articles = Article.objects.filter(prediction_id=prediction_idU).order_by('-date_scraping')[:6]

    context = {
        'prediction_name': prediction_name,
        'articles': articles,
    }
    return render(request, 'accounts/artikel.html', context)



def register(request):
    if request.user.is_authenticated:
        return redirect('templatechatbot')  # Tidak bisa akses register jika sudah login

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])  # Hash password
            user.save()
            login(request, user)  # Login otomatis setelah register
            return redirect('templatechatbot')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def register_success(request):
    return render(request, 'accounts/register_succes.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('templatechatbot')  # Tidak bisa akses login jika sudah login

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            uname = form.cleaned_data['username']
            pwd = form.cleaned_data['password']
            user = authenticate(request, username=uname, password=pwd)
            if user is not None:
                login(request, user)
                return redirect('templatechatbot')
            else:
                form.add_error(None, 'Username atau password salah')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

@login_required
def riwayat_view(request):
    user = request.user
    # Ambil semua prediksi berdasarkan user tanpa mengurutkan
    predictions = Prediction.objects.filter(user=user)
    
    context = {
        'predictions': predictions
    }
    return render(request, 'accounts/riwayat.html', context)


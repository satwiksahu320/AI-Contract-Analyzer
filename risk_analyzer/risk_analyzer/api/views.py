import json

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import ProfileForm, RegisterForm
from .models import Prediction, UserProfile
from .services.market_service import get_stock_history, get_top_company_snapshots
from .services.ml_service import predict_text_risk
from .services.news_service import get_finance_news
from .services.pdf_service import extract_pdf_text


@login_required
def dashboard(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    predictions = Prediction.objects.filter(user=request.user)
    total_predictions = predictions.count()
    high_risk_count = predictions.filter(score__gte=70).count()

    average_score = predictions.aggregate(Avg("score"))["score__avg"]
    if average_score is None:
        average_score = 0

    return render(request, "dashboard.html", {
        "profile": profile,
        "total_predictions": total_predictions,
        "high_risk_count": high_risk_count,
        "average_score": round(average_score),
    })


@login_required
@require_POST
def predict_risk(request):
    try:
        data = json.loads(request.body)
        text = data.get("text")

        if text is None or text.strip() == "":
            return JsonResponse({"error": "Text required"}, status=400)

        text = text.strip()
        prediction, score = predict_text_risk(text)

        Prediction.objects.create(
            user=request.user,
            text=text,
            prediction=prediction,
            score=score
        )

        return JsonResponse({
            "prediction": prediction,
            "score": score
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    except Exception as error:
        print(error)
        return JsonResponse({"error": "Risk analysis failed. Please try again."}, status=500)


@login_required
@require_POST
def upload_pdf(request):
    try:
        pdf_file = request.FILES.get("pdf")

        if pdf_file is None:
            return JsonResponse({"error": "No PDF uploaded"}, status=400)

        if pdf_file.size > 5 * 1024 * 1024:
            return JsonResponse({"error": "PDF size must be 5 MB or smaller."}, status=400)

        if pdf_file.name.lower().endswith(".pdf") == False:
            return JsonResponse({"error": "Only PDF files are supported."}, status=400)

        text = extract_pdf_text(pdf_file)
        prediction, score = predict_text_risk(text)

        Prediction.objects.create(
            user=request.user,
            text=text,
            prediction=prediction,
            score=score,
            uploaded_file=pdf_file
        )

        return JsonResponse({
            "prediction": prediction,
            "score": score,
            "text_preview": text[:500]
        })

    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)

    except Exception as error:
        print(error)
        return JsonResponse({"error": "PDF analysis failed. Please try again."}, status=500)


@login_required
def history_view(request):
    predictions = Prediction.objects.filter(user=request.user)
    predictions = predictions.order_by("-created_at")

    return render(request, "history.html", {
        "predictions": predictions
    })


@login_required
def market_top_view(request):
    try:
        companies = get_top_company_snapshots()

        return JsonResponse({
            "companies": companies
        })

    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=503)


@login_required
def market_search_view(request):
    symbol = request.GET.get("symbol", "")

    try:
        stock_data = get_stock_history(symbol)
        return JsonResponse(stock_data)

    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)


@login_required
def market_news_view(request):
    query = request.GET.get("q", "financial markets risk")

    try:
        articles = get_finance_news(query)

        return JsonResponse({
            "articles": articles
        })

    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=503)


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    form = ProfileForm(instance=profile)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()

    return render(request, "profile.html", {
        "form": form,
        "profile": profile
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect("/api/")

    form = RegisterForm()

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/api/")

    return render(request, "register.html", {
        "form": form
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect("/api/")

    error = ""
    form = AuthenticationForm()

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("/api/")
        else:
            error = "Invalid username or password"

    return render(request, "login.html", {
        "form": form,
        "error": error
    })


@login_required
@require_POST
def delete_profile_picture(request):
    profile = request.user.userprofile
    profile.profile_picture = "profiles/default.png"
    profile.save()

    return redirect("/api/profile/")


@login_required
@require_POST
def delete_account(request):
    user = request.user

    logout(request)
    user.delete()

    return redirect("/api/register/")


def logout_view(request):
    logout(request)
    return redirect("/api/login/")

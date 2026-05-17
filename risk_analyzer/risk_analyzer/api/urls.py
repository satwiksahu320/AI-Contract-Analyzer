from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('predict/', views.predict_risk, name='predict_risk'),
    path('upload-pdf/', views.upload_pdf, name='upload_pdf'),
    path('history/', views.history_view, name='history'),
    path('market/top/', views.market_top_view, name='market_top'),
    path('market/search/', views.market_search_view, name='market_search'),
    path('news/', views.market_news_view, name='market_news'),
    path('profile/', views.profile_view, name='profile'),
    path('delete-profile-pic/', views.delete_profile_picture, name='delete_profile_picture'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

"""ClashRCRound2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views
from django.views.decorators.cache import never_cache

urlpatterns = [
    path('', views.register, name="register"),
    path('login/', views.login, name="login"),
    path('timer/', views.set_timer, name='timer'),
    path('question-hub/', never_cache(views.question_hub), name='question-hub'),
    path('question/<int:pk>', never_cache(views.coding_page), name='coding-page'),
    path('submissions-page/', never_cache(views.submission_page), name='submissions-page'), # do not add never_cache for this one
    path('leaderboard/', never_cache(views.leaderboard), name='leaderboard'),
    path('logout/', never_cache(views.logout), name='logout'),
    path('submission_<int:submission_id>/', never_cache(views.view_submission), name='view-submission'),
    path('load-buffer/', views.load_buffer, name='loadbuffer'),
    path('get-output/', views.get_output, name='get-output'),
]

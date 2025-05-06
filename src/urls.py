"""
URL configuration for assistant project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from assistants.onomi import views as onomi_views

urlpatterns = [
    path('admin/', admin.site.urls),
    #ONOMI Urls
    path('onomi', onomi_views.onomi, name='onomi'),
    path('retrieve_messages', onomi_views.retrieve_messages, name='retrieve_messages'),
    path('audio_transcribe', onomi_views.audio_transcribe, name='audio_transcribe'),
]

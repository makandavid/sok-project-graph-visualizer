"""
URL configuration for graph_explorer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.new_workspace, name='new_workspace'),
    path('workspace/<str:workspace_id>/', views.index, name='index'),

    path('upload-graph/<str:workspace_id>/', views.upload_graph, name='upload_graph'),
    path('search/<str:workspace_id>/', views.search_filter, name="search"),
    path('reset/<str:workspace_id>/', views.reset_filter, name="reset"),
    path('change_visualization_plugin/<str:workspace_id>/', views.change_visualization_plugin, name='change_visualization_plugin'),
    path('rename/<str:workspace_id>/', views.rename_workspace, name='rename_workspace'),
    path("cli/execute/", views.cli_execute, name="cli_execute"),

]

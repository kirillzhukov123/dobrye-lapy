from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('pets/', views.pet_list, name='pet_list'),
    path('api/pets/', views.api_pets, name='api_pets'),
    path('search/', views.search, name='search'),
    path('pets/add/', views.pet_create, name='pet_create'),
    path('pets/<int:pk>/', views.pet_detail, name='pet_detail'),
    path('pets/<int:pk>/edit/', views.pet_edit, name='pet_edit'),
    path('pets/<int:pk>/delete/', views.pet_delete, name='pet_delete'),
    path('pets/<int:pk>/apply/', views.apply_adoption, name='apply_adoption'),
    path('pets/<int:pk>/walk/', views.book_walk, name='book_walk'),
    path('applications/', views.application_list, name='application_list'),
    path('applications/<int:pk>/approve/', views.approve, name='approve'),
    path('applications/<int:pk>/reject/', views.reject_application, name='reject_application'),
    path('walks/<int:pk>/done/', views.walk_done, name='walk_done'),
    path('guardianship/', views.guardianship, name='guardianship'),
]

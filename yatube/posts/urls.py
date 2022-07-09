from django.urls import path

from . import views

app_name = 'posts'

urlpatterns = [
    path('posts/<int:post_id>/comment', views.add_comment, name='add_comment'),
    path('posts/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    path(
        'profile/<str:username>/follow/',
        views.profile_follow,
        name='profile_follow',
    ),
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow',
    ),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('group/<slug:slug>/', views.group_list, name='group_list'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('follow/', views.follow_index, name='follow_index'),
    path('create/', views.post_create, name='post_create'),
    path('account/<str:username>', views.user_account, name='user_account'),
    path('', views.index, name='index'),
]

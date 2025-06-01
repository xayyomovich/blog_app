from django.urls import path
from . import views
# from .views import PostListView

app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='post_list'),   # ------------FBV
    # path('', views.PostListView.as_view(), name='post_list'),
    path('tag/<slug:tag_slug>/', views.post_list, name = 'post_list_by_tag'),

    path('<int:year>/<int:month>/<int:day>/<slug:post>/',
         views.post_detail, name='post_detail'),

    path('<int:post_id>/share/', views.post_share, name='post_share'),
    path('<int:post_id>/comment/', views.post_comment, name='post_comment'),

    # path('<int:year>/<int:month>/<int:day>/<slug:post>/',
    #      views.post_detail, name='post_detail')    #------------- FBV

    # New API endpoints
    path('api/translate-pirate/', views.translate_to_pirate, name='translate_pirate'),
    path('api/gemini-chat/', views.gemini_chat, name='gemini_chat'),

    # New AI chat page
    path('ai-chat/', views.ai_chat_page, name='ai_chat'),
]















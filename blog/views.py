from django.shortcuts import render, get_object_or_404
from .models import Post
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count
from django.http import JsonResponse
import requests
import json
from django.conf import settings
import google.generativeai as genai


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    print(post)
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = ("Subject: "
                       f"{cd['name']} ({cd['email']}) recommends you to read {post.title}")
            message = (f"Message: "
                       f"Read {post.title} at {post_url}\n\n"
                       f"{cd['name']}\'s comment: {cd['comments']}")
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[cd['to']]
            )
            sent = True
    else:
        form = EmailPostForm()
    return render(
        request,
        'blog/post/share.html',
        {
            'post': post,
            'form': form,
            'sent': sent
        })


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
    return render(request, 'blog/post/comment.html', {'post': post, 'form': form, 'comment': comment})


def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)   # paginator.num_pages is a property of the Paginator object that returns the total number of pages
    return render(request, 'blog/post/list.html', context={'posts': posts, 'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, status=Post.Status.PUBLISHED, slug=post,
                             publish__year=year, publish__month=month, publish__day=day)
    # List of active comments for this post
    comments = post.comments.filter(active=True)
    # Form for users to comment
    form = CommentForm()
    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(
        tags__in=post_tags_ids
    ).exclude(id=post.id)
    similar_posts = similar_posts.annotate(
        same_tags=Count('tags')
    ).order_by('-same_tags', '-publish')[:4]
    return render(request, 'blog/post/detail.html',
                  context={'post': post,
                           'comments': comments,
                           'form': form,
                           'similar_posts': similar_posts})


# New view for pirate translation
def translate_to_pirate(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text_to_translate = data.get('text', '')

            if not text_to_translate:
                return JsonResponse({'error': 'No text provided'}, status=400)

            # Call Fun Translations API
            response = requests.post(
                'https://api.funtranslations.com/translate/pirate.json',
                data={'text': text_to_translate},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                translated_text = result.get('contents', {}).get('translated', '')
                return JsonResponse({'translated': translated_text})
            else:
                return JsonResponse({'error': 'Translation service unavailable'}, status=503)

        except requests.RequestException:
            return JsonResponse({'error': 'Translation service error'}, status=503)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request format'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


# New view for Gemini AI chat
def gemini_chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_question = data.get('question', '')

            if not user_question:
                return JsonResponse({'error': 'No question provided'}, status=400)

            # Prepare API call
            api_key = settings.GEMINI_API_KEY
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

            headers = {
                "Content-Type": "application/json"
            }

            body = {
                "contents": [
                    {
                        "parts": [
                            {"text": user_question}
                        ]
                    }
                ]
            }

            response = requests.post(url, headers=headers, json=body)
            if response.status_code != 200:
                return JsonResponse({'error': 'Gemini API error', 'details': response.text}, status=response.status_code)

            result = response.json()
            generated_text = result['candidates'][0]['content']['parts'][0]['text']

            return JsonResponse({'response': generated_text})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request format'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


# New view to render the AI chat page
def ai_chat_page(request):
    return render(request, 'blog/ai_chat.html')


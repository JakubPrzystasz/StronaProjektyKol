from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from papers.models import Message, MessageSeen, Paper


class TestView(TemplateView):
    template_name = "messaging/messagebox.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paper = Paper.objects.filter(pk=self.kwargs['paper_pk']).first()

        if paper is None:
            return context
        user = self.request.user

        if not has_user_access_to_messages(user, paper):
            return context

        context['username'] = user.username
        context['paper_id'] = self.kwargs['paper_pk']
        context['reviewer_id'] = self.kwargs['reviewer_pk']
        return context


@csrf_exempt
def render_message(request):
    return render(request, 'messaging/message.html', {
        'type': request.POST['type'],
    })


@csrf_exempt
def get_message(request):
    user = request.user
    paper = Paper.objects.filter(pk=request.POST['paper_id']).first()

    if has_user_access_to_messages(user, paper):
        last_message_id = int(request.POST['last_message_id'])
        messages = Message.objects.filter(paper=paper, pk__gt=last_message_id).order_by('created_at')
        data = dict()
        for message in messages:
            tmp = {'author': f'{message.author.username}',
                   'author_name': f'{message.author.first_name} {message.author.last_name}',
                   'date': f'{message.created_at.strftime("%d %b %H:%M")}', 'text': f'{message.text}',
                   'id': f'{message.id}'}
            data[message.pk] = tmp

            # add seen record
            if message.author == user:
                continue

            if MessageSeen.objects.filter(message=message, reader=user).first() is None:
                MessageSeen.objects.create(
                    message=message,
                    reader=request.user,
                )

        return JsonResponse(data)
    else:
        response = HttpResponse()
        response.status_code = 401
        return response


@csrf_exempt
def send_message(request):
    response = HttpResponse()

    if request.method == "POST":
        user = request.user
        paper = Paper.objects.filter(pk=request.POST['paper_id']).first()
        reviewer = User.objects.filter(pk=request.POST['reviewer_id']).first()

        if reviewer is None:
            response.status_code = 400

        if has_user_access_to_messages(user, paper):
            Message.objects.create(
                author=user,
                paper=paper,
                reviewer=reviewer,
                text=request.POST['message_text'],
            )
            response.status_code = 200
        else:
            response.status_code = 400
    else:
        response.status_code = 401

    return response


def has_user_access_to_messages(user, paper):
    if paper is None or not user.is_authenticated:
        return False

    if not user.is_staff and user not in paper.reviewers.all() and user not in paper.authors.all():
        return False

    return True

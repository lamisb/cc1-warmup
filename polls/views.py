# polls/views.py
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.contrib import messages  # optional but recommended

from .models import Choice, Question


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"
    paginate_by = 10  # pagination

    def get_queryset(self):
        """
        Return published questions (not future-dated), ordered by most recent.
        Supports a simple search via ?q=...
        """
        qs = Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")
        q = self.request.GET.get("q")
        if q:
            # Adjust fields to match your Question model (e.g., 'question_text')
            qs = qs.filter(Q(question_text__icontains=q) | Q(id__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        # Keep the search query in the context so templates can preserve it in pagination links
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        return context


class DetailView(generic.DetailView):
    """
    Detail page should not show future-dated questions.
    """
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    """
    Results page should not show future-dated questions either.
    """
    model = Question
    template_name = "polls/results.html"

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.now())


def vote(request, question_id):
    """
    Handles voting:
    - Prevents duplicate votes per session per question
    - Uses F() expressions inside a transaction for concurrency safety
    - Gives friendly error messages and redirects properly
    """
    if request.method != "POST":
        # Only allow POST to avoid accidental re-votes via GET
        return HttpResponseNotAllowed(["POST"])

    question = get_object_or_404(
        Question.objects.filter(pub_date__lte=timezone.now()),
        pk=question_id,
    )

    # Simple duplicate-vote guard using session
    voted_questions = request.session.get("voted_questions", [])
    if question.id in voted_questions:
        messages.warning(request, "You have already voted on this question.")  # optional
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))

    try:
        choice_ids = request.POST.getlist("choice")
        if not choice_ids:
            raise KeyError("No choices selected")
        
        # Validate that all selected choices belong to this question
        selected_choices = question.choice_set.filter(pk__in=choice_ids)
        if len(selected_choices) != len(choice_ids):
            raise Choice.DoesNotExist("Invalid choice selected")
            
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form with an error
        messages.error(request, "You didn't select any valid choices.")  # optional
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select any valid choices.",
            },
        )

    # Concurrency-safe increment for all selected choices
    with transaction.atomic():
        for choice in selected_choices:
            Choice.objects.filter(pk=choice.pk).update(votes=F("votes") + 1)

    # Mark this question as voted in the session
    voted_questions.append(question.id)
    request.session["voted_questions"] = voted_questions

    choice_count = len(selected_choices)
    if choice_count == 1:
        messages.success(request, "Thanks for voting!")
    else:
        messages.success(request, f"Thanks for voting! You selected {choice_count} choices.")  # optional
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))

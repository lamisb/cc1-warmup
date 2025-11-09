from django.contrib import admin
from .models import Question, Choice

# Inline display for choices within the Question edit page
class ChoiceInline(admin.TabularInline):  # you can also use admin.StackedInline
    model = Choice
    extra = 1  # show 1 empty field by default
    min_num = 0
    can_delete = True

# Custom Question admin with inlines
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "pub_date")
    search_fields = ("question_text",)
    inlines = [ChoiceInline]

# Trying to register Choice separately to edit them directly in admin
@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("choice_text", "question", "votes")
    list_filter = ("question",)
    search_fields = ("choice_text",)

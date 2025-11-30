from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import Test, Question, Answer, StudentTest, StudentAnswer


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    max_num = 4
    min_num = 2
    fields = ['text', 'is_correct', 'letter']
    verbose_name = 'Вариант ответа'
    verbose_name_plural = 'Варианты ответов'


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['title', 'question_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description')
        }),
        ('Настройки теста', {
            'fields': ('question_count', 'is_active')
        }),
        ('Дата создания', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'test', 'order']
    list_filter = ['test']
    search_fields = ['text']
    inlines = [AnswerInline]
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст вопроса'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['letter', 'text_preview', 'is_correct', 'question']
    list_filter = ['is_correct', 'question__test']
    search_fields = ['text']
    
    def text_preview(self, obj):
        return obj.text[:30] + "..." if len(obj.text) > 30 else obj.text
    text_preview.short_description = 'Текст ответа'


@admin.register(StudentTest)
class StudentTestAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'student_class', 'test', 'score', 'total_questions', 'percentage', 'started_at', 'completed_at']
    list_filter = ['student_class', 'test', 'started_at']
    search_fields = ['student_name']
    readonly_fields = ['score', 'total_questions', 'percentage', 'started_at', 'completed_at']
    
    def percentage(self, obj):
        return f"{obj.percentage:.2f}%"
    percentage.short_description = 'Процент правильных ответов'


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['student_test', 'question_preview', 'selected_answer', 'is_correct']
    list_filter = ['is_correct', 'student_test__test']
    search_fields = ['student_test__student_name', 'question__text']
    
    def question_preview(self, obj):
        return obj.question.text[:30] + "..." if len(obj.question.text) > 30 else obj.question.text
    question_preview.short_description = 'Вопрос'

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import random


class Test(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название теста')
    description = models.TextField(blank=True, verbose_name='Описание')
    question_count = models.PositiveIntegerField(
        default=5, 
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name='Количество вопросов в тесте'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    
    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions', verbose_name='Тест')
    text = models.TextField(verbose_name='Текст вопроса')
    order = models.PositiveIntegerField(default=1, verbose_name='Порядковый номер')
    
    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['order']
    
    def __str__(self):
        text_preview = str(self.text)[:50] if self.text else ""
        return f'Вопрос {self.order}: {text_preview}...'


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='Вопрос')
    text = models.CharField(max_length=500, verbose_name='Текст ответа')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    letter = models.CharField(max_length=1, choices=[
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ], verbose_name='Буква ответа')
    
    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'
        ordering = ['letter']
    
    def __str__(self):
        text_preview = str(self.text)[:30] if self.text else ""
        return f'{self.letter}. {text_preview}...'


class StudentTest(models.Model):
    student_name = models.CharField(max_length=100, verbose_name='ФИО ученика')
    student_class = models.CharField(max_length=20, verbose_name='Класс')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name='Тест')
    score = models.PositiveIntegerField(default=0, verbose_name='Количество правильных ответов')
    total_questions = models.PositiveIntegerField(default=0, verbose_name='Общее количество вопросов')
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Процент правильных ответов')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Начат')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Завершен')
    
    class Meta:
        verbose_name = 'Прохождение теста'
        verbose_name_plural = 'Прохождения тестов'
        ordering = ['-started_at']
    
    def __str__(self):
        test_title = str(self.test.title) if self.test and hasattr(self.test, 'title') else "Тест"
        return f'{self.student_name} - {test_title}'
    
    def calculate_percentage(self):
        if self.total_questions > 0:
            self.percentage = (self.score / self.total_questions) * 100
            return self.percentage
        return 0


class StudentAnswer(models.Model):
    student_test = models.ForeignKey(StudentTest, on_delete=models.CASCADE, related_name='student_answers', verbose_name='Прохождение теста')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='Вопрос')
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, verbose_name='Выбранный ответ')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    
    class Meta:
        verbose_name = 'Ответ ученика'
        verbose_name_plural = 'Ответы учеников'
    
    def __str__(self):
        student_name = str(self.student_test.student_name) if self.student_test and hasattr(self.student_test, 'student_name') else "Ученик"
        question_text = str(self.question.text)[:30] if self.question and hasattr(self.question, 'text') else "Вопрос"
        return f'{student_name} - {question_text}...'

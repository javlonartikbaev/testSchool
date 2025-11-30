from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.utils import timezone
import random
from .models import Test, Question, Answer, StudentTest, StudentAnswer


def home(request):
    """Главная страница со списком доступных тестов"""
    tests = Test.objects.filter(is_active=True)
    return render(request, 'quiz/home.html', {'tests': tests})


def start_test(request, test_id):
    """Начать тест"""
    test = get_object_or_404(Test, id=test_id, is_active=True)
    
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        student_class = request.POST.get('student_class')
        
        if not student_name or not student_class:
            messages.error(request, 'Пожалуйста, заполните все поля')
            return render(request, 'quiz/start_test.html', {'test': test})
        
        # Создаем запись о прохождении теста
        student_test = StudentTest.objects.create(
            student_name=student_name,
            student_class=student_class,
            test=test,
            total_questions=test.question_count
        )
        
        # Выбираем случайные вопросы
        all_questions = list(test.questions.all())
        if len(all_questions) < test.question_count:
            messages.error(request, f'Недостаточно вопросов в тесте. Доступно: {len(all_questions)}, требуется: {test.question_count}')
            student_test.delete()
            return render(request, 'quiz/start_test.html', {'test': test})
        
        selected_questions = random.sample(all_questions, test.question_count)
        
        # Сохраняем выбранные вопросы в сессии
        request.session[f'questions_{student_test.id}'] = [q.id for q in selected_questions]
        request.session[f'student_test_{student_test.id}'] = student_test.id
        
        return redirect('quiz_question', student_test_id=student_test.id, question_num=1)
    
    return render(request, 'quiz/start_test.html', {'test': test})


def quiz_question(request, student_test_id, question_num):
    """Страница с вопросом"""
    student_test = get_object_or_404(StudentTest, id=student_test_id)
    
    # Проверяем, что вопросы были выбраны
    if f'questions_{student_test_id}' not in request.session:
        messages.error(request, 'Ошибка сессии. Начните тест заново.')
        return redirect('home')
    
    question_ids = request.session[f'questions_{student_test_id}']
    total_questions = len(question_ids)
    
    if question_num > total_questions:
        return redirect('quiz_finish', student_test_id=student_test_id)
    
    question_id = question_ids[question_num - 1]
    question = get_object_or_404(Question, id=question_id)
    answers = question.answers.all()
    
    # Перемешиваем варианты ответов
    answers = list(answers)
    random.shuffle(answers)
    
    context = {
        'student_test': student_test,
        'question': question,
        'answers': answers,
        'question_num': question_num,
        'total_questions': total_questions,
        'progress': (question_num / total_questions) * 100
    }
    
    return render(request, 'quiz/question.html', context)


def submit_answer(request, student_test_id, question_num):
    """Обработка ответа на вопрос"""
    if request.method != 'POST':
        return redirect('quiz_question', student_test_id=student_test_id, question_num=question_num)
    
    student_test = get_object_or_404(StudentTest, id=student_test_id)
    answer_id = request.POST.get('answer_id')
    
    if not answer_id:
        messages.error(request, 'Пожалуйста, выберите ответ')
        return redirect('quiz_question', student_test_id=student_test_id, question_num=question_num)
    
    # Получаем вопрос
    question_ids = request.session[f'questions_{student_test_id}']
    question_id = question_ids[question_num - 1]
    question = get_object_or_404(Question, id=question_id)
    
    # Получаем выбранный ответ
    answer = get_object_or_404(Answer, id=answer_id)
    
    # Проверяем, правильный ли ответ
    is_correct = answer.is_correct
    
    # Сохраняем ответ ученика
    StudentAnswer.objects.create(
        student_test=student_test,
        question=question,
        selected_answer=answer,
        is_correct=is_correct
    )
    
    # Обновляем счетчик правильных ответов
    if is_correct:
        student_test.score += 1
        student_test.save()
    
    # Переходим к следующему вопросу или завершаем тест
    if question_num < len(question_ids):
        return redirect('quiz_question', student_test_id=student_test_id, question_num=question_num + 1)
    else:
        return redirect('quiz_finish', student_test_id=student_test_id)


def quiz_finish(request, student_test_id):
    """Завершение теста и показ результатов"""
    student_test = get_object_or_404(StudentTest, id=student_test_id)
    
    # Вычисляем процент правильных ответов
    student_test.calculate_percentage()
    student_test.completed_at = timezone.now()
    student_test.save()
    
    # Удаляем данные из сессии
    if f'questions_{student_test_id}' in request.session:
        del request.session[f'questions_{student_test_id}']
    if f'student_test_{student_test_id}' in request.session:
        del request.session[f'student_test_{student_test_id}']
    
    # Получаем детальные результаты
    student_answers = student_test.student_answers.all()
    
    # Вычисляем количество неправильных ответов
    wrong_answers = student_test.total_questions - student_test.score
    
    context = {
        'student_test': student_test,
        'student_answers': student_answers,
        'correct_answers': student_test.score,
        'wrong_answers': wrong_answers,
        'total_questions': student_test.total_questions,
        'percentage': student_test.percentage
    }
    
    return render(request, 'quiz/finish.html', context)


def test_results(request):
    """Страница с результатами всех тестов (для просмотра администратором)"""
    student_tests = StudentTest.objects.all().order_by('-started_at')
    
    # Фильтрация по ученику, классу или тесту
    student_name = request.GET.get('student_name')
    student_class = request.GET.get('student_class')
    test_id = request.GET.get('test')
    
    if student_name:
        student_tests = student_tests.filter(student_name__icontains=student_name)
    if student_class:
        student_tests = student_tests.filter(student_class__icontains=student_class)
    if test_id:
        student_tests = student_tests.filter(test_id=test_id)
    
    # Пагинация
    paginator = Paginator(student_tests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'tests': Test.objects.all(),
        'current_filters': {
            'student_name': student_name,
            'student_class': student_class,
            'test': test_id
        }
    }
    
    return render(request, 'quiz/results.html', context)

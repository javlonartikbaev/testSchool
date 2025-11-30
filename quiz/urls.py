from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('test/<int:test_id>/', views.start_test, name='start_test'),
    path('quiz/<int:student_test_id>/<int:question_num>/', views.quiz_question, name='quiz_question'),
    path('submit/<int:student_test_id>/<int:question_num>/', views.submit_answer, name='submit_answer'),
    path('finish/<int:student_test_id>/', views.quiz_finish, name='quiz_finish'),
    path('results/', views.test_results, name='test_results'),
]

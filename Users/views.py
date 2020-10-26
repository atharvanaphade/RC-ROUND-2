import datetime
import os
import re
import subprocess
import json
import math

from django.contrib import auth, messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, reverse

from Sandbox.views import user_ka_aukaat_check_kar
from .models import Profile, Question, Submissions

start_time = 0
end_time = 0
duration = 0
flag = False
start = datetime.datetime(2020, 1, 1, 0, 0)

USER_CODE_PATH = 'data/users_code/'
STANDARD = 'data/standard/'

NO_OF_QUESTIONS = 6
NO_OF_TEST_CASES = 6


def set_timer(request):
    if request.user.is_superuser:
        if request.method == 'GET':
            return render(request, 'Users/timer.html')
        elif request.method == 'POST':
            global start_time, start
            global end_time
            global duration
            global flag
            flag = True
            duration = request.POST.get('duration')  # duration = 7200
            start = datetime.datetime.now()
            start = start + datetime.timedelta(0, 15)
            time = start.second + start.minute * 60 + start.hour * 60 * 60
            start_time = time
            end_time = time + int(duration)
            return HttpResponse(" time is set ")
    return HttpResponse("You cannot access this URL.")


def remaining_time(request):
    time = datetime.datetime.now()
    now = (time.hour * 60 * 60) + (time.minute * 60) + time.second
    global end_time
    if now < end_time:
        time_left = end_time - now
        return time_left
    else:
        return 0


def leaderboard(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            questions = Question.objects.all()
            current_user = request.user.username
            current_score = request.user.profile.totalScore
            leaderboard = {}
            for profile in Profile.objects.order_by('-totalScore'):
                question_scores = [0 for i in questions]
                user_submissions = Submissions.objects.filter(userID=profile.user.id)
                if user_submissions:
                    for question in questions:
                        question_submission = user_submissions.filter(quesID=question.id)
                        if question_submission:
                            question_score = question_submission.order_by('-score').first()
                            question_scores[question.id - 1] += question_score.score
                question_scores.append(profile.totalScore)
                leaderboard[profile.user.username] = question_scores
            rank = list(leaderboard.keys()).index(current_user)
            paginator = Paginator(tuple(leaderboard.items()), 10)  # Show 10 users per page.
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            page_range = paginator.page_range
            user_accuracy = round(((request.user.profile.correctly_answered / len(questions)) * 100), 2)
            time = remaining_time(request)
            context = {'questions': questions, 'page_obj': page_obj, 'current_user': current_user,
                       'current_user_score': current_score, 'current_user_rank': rank + 1, 'page_range': page_range,
                       'time': time, 'user_accuracy': user_accuracy}
            return render(request, 'Users/leaderboard.html', context)
        else:
            return HttpResponse("Invalid request type.")
    messages.error(request, 'You must login to view this page.')
    return HttpResponseRedirect(reverse("login"))


def question_hub(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            # users = User.objects.all()
            questions = Question.objects.all()
            avg_accuracies = []
            for question in questions:
                try:
                    accuracy = round(((question.successfulAttempts / question.numberOfAttempts) * 100), 2)
                except ZeroDivisionError:
                    accuracy = 0
                avg_accuracies.append(accuracy)
            time = remaining_time(request)
            if time != 0:
            context = {'group': zip(questions, avg_accuracies), 'time': time}
            return render(request, 'Users/question_hub.html', context)
            else:
            return render(request, 'Users/final_result.html')
        else:
            return HttpResponse("Invalid request type.")
    messages.error(request, 'You must login to view this page.')
    return HttpResponseRedirect(reverse("login"))


def submission_page(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            pk = 1
            submissions = Submissions.objects.filter(userID=request.user.id, quesID=pk)
            time = remaining_time(request)
            context = {'submissions': submissions, 'time': time}
            return render(request, "Users/submissions.html", context)
        elif request.method == 'POST':
            pk = request.POST.get('selected')
            question = Question.objects.get(pk=pk)
            submissions = Submissions.objects.filter(userID=request.user.id, quesID=question.id)
            time = remaining_time(request)
            context = {'submissions': submissions, 'time': time}
            return render(request, 'Users/submissions.html', context)
        else:
            return HttpResponse("Invalid request type.")
    messages.error(request, 'You must login to view this page.')
    return HttpResponseRedirect(reverse("login"))


def view_submission(request, submission_id):
    if request.user.is_authenticated:
        if request.method == 'GET':
            user_profile = Profile.objects.get(user=request.user)
            submission = Submissions.objects.get(id=submission_id)
            code = json.dumps(submission.code)
            question = Question.objects.get(pk=submission.quesID.pk)
            user = request.user
            timer = remaining_time(request)
            context = {'question': question, 'user': user, 'time': timer,
                       'total_score': user_profile.totalScore, 'question_id': submission.quesID.pk,
                       'code': code}
            return render(request, 'Users/coding_page.html', context)
        else:
            return HttpResponse("Invalid request type.")
    messages.error(request, 'You must login to view this page.')
    return HttpResponseRedirect(reverse("login"))


def modify_file_contents(code, extension, code_file_path):
    if extension != 'py':
        sandbox_header = '#include"../../../include/sandbox.h"\n'
        try:
            # Inject the function call for install filters in the user code file
            # Issue with design this way (look for a better solution (maybe docker))
            # multiple main strings
            before_main = code.split('main')[0] + 'main'
            after_main = code.split('main')[1]
            index = after_main.find('{') + 1
            main = before_main + after_main[:index] + 'install_filters();' + after_main[index:]
            with open(code_file_path, 'w+') as f:
                f.write(sandbox_header)
                f.write(main)
                f.close()
        except IndexError:
            with open(code_file_path, 'w+') as f:
                f.write(code)
                f.close()
    else:
        with open(code_file_path, 'w+') as f:
            f.write('import temp\n')
            f.write(code)
            f.close()


def coding_page(request, pk):
    if request.user.is_authenticated:
        if request.method == 'GET':
            que = Question.objects.get(pk=pk)
            user_profile = Profile.objects.get(user=request.user)
            user = request.user
            timer = remaining_time(request)
            # if timer != 0:
            context = {'question': que, 'user': user, 'time': timer,
                       'total_score': user_profile.totalScore,
                       'question_id': pk,
                       'junior': user_profile.junior}
            return render(request, 'Users/coding_page.html', context)
            # return render(request, 'Users/result.html')  # result page?

        elif request.method == 'POST':
            username = request.user.username
            current_question = Question.objects.get(pk=pk)
            ext = request.POST['ext']
            code = request.POST['code']
            if Submissions.objects.filter(userID=request.user.id, quesID=current_question).exists():
                submissions = Submissions.objects.filter(userID=request.user.id, quesID=current_question.pk)
                data = {}
                for submission in submissions:
                    if submission.status == 'PASS':
                        # messages.error(request, "You have already scored the maximum possible sscore for this question.")
                        # data = "You have already scored the maximum possible score for this question."
                        data['message'] = "You have already scored the maximum possible marks for this question. \nYou cannot attempt this question again."
                        return JsonResponse(data)
                submission = submissions.order_by('-attempt').first()
                attempt = submission.attempt + 1
                submission = submissions.order_by('-accuracy').first()
            else:
                attempt = 1
            user_question_path = '{}{}/question{}/'.format(USER_CODE_PATH, username, pk)
            if not os.path.exists(user_question_path):
                os.system('mkdir ' + user_question_path)
            code_file = user_question_path + "code{}.{}".format(attempt, ext)
            code = str(code)
            modify_file_contents(code, ext, code_file)
            testcase_values = user_ka_aukaat_check_kar(username=username, question_number=pk, attempts=attempt,
                                        ext=ext)
            code_f = open(code_file, 'w+')
            code_f.seek(0)
            code_f.write(code)
            code_f.close()
            global end_time
            time = datetime.datetime.now()
            submission_time_sec = time.second + time.minute * 60 + time.hour * 60 * 60
            global start_time
            submission_time = end_time - submission_time_sec

            hours = math.floor(submission_time / 3600)
            minutes = math.floor(submission_time % 3600 / 60)
            seconds = math.floor(submission_time % 3600 % 60)

            if (hours   < 10):
                hours   = "0" + str(hours)
            if (minutes < 10):
                minutes = "0" + str(minutes)
            if (seconds < 10):
                seconds = "0" + str(seconds)

            final_submission_time = '{}:{}:{}'.format(hours, minutes, seconds)

            error_text = ""
            epath = USER_CODE_PATH + '/{}/question{}/error.txt'.format(username, pk)
            if os.path.exists(epath):
                ef = open(epath, 'r')
                error_text = ef.read()
                error_text = re.sub('/.*?:', '', error_text)  # regular expression
                ef.close()
            if error_text == "":
                error_text = "Compiled successfully."
            no_of_pass = 0
            for i in testcase_values:
                if i == 'AC':
                    no_of_pass += 1
            current_accuracy = round(((no_of_pass / NO_OF_TEST_CASES) * 100), 2)
            status = 'PASS' if no_of_pass == NO_OF_TEST_CASES else 'FAIL'
            new_submission = Submissions(quesID=current_question, userID=request.user, language=ext,
                                         code=code, attempt=attempt, submission_time=final_submission_time,
                                         accuracy=current_accuracy, status=status)
            new_submission.save()
            if status == 'PASS':
                current_question.successfulAttempts += 1
                current_question.numberOfAttempts += 1
                current_question.save()
                user_profile = Profile.objects.get(user=request.user)
                user_profile.totalScore += 100
                user_profile.correctly_answered += 1
                user_profile.save()
                new_submission.score = 100
                new_submission.save()
            else:
                current_question.numberOfAttempts += 1
                current_question.save()
            #print(testcase_values)
            #print(status)
            timer = remaining_time(request)
            data = {
                'testcases': testcase_values,
                'error': error_text,
                'status': status,
                'score': new_submission.score,
                'time': timer,
                'question_id': pk,
            }
            return render(request, "Users/test_cases.html", data)
        else:
            return HttpResponse("Invalid request type.")
    messages.error(request, 'You must login to view this page.')
    return HttpResponseRedirect(reverse("login"))


def register(request):
    if request.method == 'POST':

        username_regex = '^(?=.{4,20}$)(?:[a-zA-Z\d]+(?:(?:\.|-|_)[a-zA-Z\d])*)+$'
        username = request.POST.get('username')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'This username already exists. Try another username.')
            return render(request, 'Users/register.html')
        if not re.search(username_regex, username):
            messages.error(request, 'Please enter a valid username.')
            return render(request, 'Users/register.html')

        email_regex = '^((([!#$%&\'*+\-/=?^_`{|}~\w])|([!#$%&\'*+\-/=?^_`{|}~\w][!#$%&\'*+\-/=?^_`{|}~\.\w]{0,}[!#$%&\'*+\-/=?^_`{|}~\w]))[@]\w+([-.]\w+)*\.\w+([-.]\w+)*)$'
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already associated with another username.')
            return render(request, 'Users/register.html')
        if not re.search(email_regex, email):
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'Users/register.html')

        # phone_regex = '^(\+\d{1,2}\s?)?1?\-?\.?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$'
        phone = request.POST.get('phone')
        if (len(str(phone)) != 10 | str(phone).isnumeric() == False):
            messages.error(request, 'Please enter a valid phone number.')
            return render(request, 'Users/register.html')

        password_regex = '^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 != password2:
            messages.error(request, 'Passwords don\'t match.')
            return render(request, 'Users/register.html')
        if not re.search(password_regex, password1):
            messages.error(request,
                           'Password must contain minimum eight characters, at least one letter, one number and one special character.')
            return render(request, 'Users/register.html')

        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        college = request.POST.get('college')
        # gender = request.POST.get('gender')
        newUser = User.objects.create_user(username=username, email=email, first_name=fname, last_name=lname,
                                           password=password1)
        newUser.save()
        profile = Profile(user=newUser, phone=phone, college=college)
        profile.save()

        user_directory = "{}{}/".format(USER_CODE_PATH, username)
        if not os.path.exists(user_directory):
            os.system('mkdir ' + user_directory)
        messages.success(request, 'Your account has been created.')
        return redirect('login')
    elif request.method == 'GET':
        return render(request, 'Users/register.html')
    return HttpResponse("Invalid request type.")


def login(request):
    if request.method == 'POST':
        junior = request.POST.get('optradio')
        if not junior:
            messages.error(request, 'Please select your category.')
            return render(request, 'Users/login.html')
        time = datetime.datetime.now()
        now = (time.hour * 60 * 60) + (time.minute * 60) + time.second
        global end_time
        # if now < end_time:
        username = request.POST.get('username')
        password = request.POST.get('password')
        

        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            request.session.set_expiry(remaining_time(request))
            return render(request, 'Users/Instructions.html')
        else:
            messages.error(request, 'Invalid credentials.')
            return redirect('login')
        # messages.error(request, 'Time is up. You cannot login now')
        # return render(request, 'Users/login.html')
    elif request.method == 'GET':
        return render(request, 'Users/login.html')
    return HttpResponse("Invalid request type.")


def logout(request):
    if request.user.is_authenticated:
        questions = Question.objects.all()
        current_user = request.user.username
        current_score = request.user.profile.totalScore
        leaderboard = {}
        for profile in Profile.objects.order_by('-totalScore'):
            leaderboard[profile.user.username] = profile.totalScore
        rank = list(leaderboard.keys()).index(current_user)
        current_user_profile = Profile.objects.get(user=request.user)
        correct = current_user_profile.correctly_answered
        attempted = 0
        for question in questions:
            if Submissions.objects.filter(userID=request.user.id, quesID=question.pk).exists():
                attempted += 1
        context = {'leaderboard' : leaderboard, 'username': current_user, 'rank': rank + 1, 'score': current_score,
                    'questions_solved': correct, 'questions_attempted': attempted}
        auth.logout(request)
        return render(request, 'Users/result rc.html', context)
    return redirect('login')


def load_buffer(request):
    if not request.user.is_authenticated:
        messages.error(request, 'You must login first.')
        return HttpResponseRedirect(reverse("login"))
    if not request.is_ajax:
        return HttpResponse("Invalid request type.")
    if request.user.is_authenticated and request.is_ajax():
        question_number = request.POST.get('qno')
        question = Question.objects.get(pk=question_number)
        txt = ""
        submissions = Submissions.objects.filter(userID=request.user.id, quesID=question.id).order_by(
            '-attempt').first()
        if submissions:
            code_file = USER_CODE_PATH + '{}/question{}/code{}.{}'.format(request.user.username, question_number,
                                                                          submissions.attempt, submissions.language)
            f = open(code_file, "r")
            txt = f.read()
            f.close()
        response_data = {'txt': txt}
        return JsonResponse(response_data)
    


def get_output(request):
    if not request.user.is_authenticated:
        messages.error(request, 'You must login first.')
        return HttpResponseRedirect(reverse("login"))
    if not request.is_ajax:
        return HttpResponse("Invalid request type.")
    if request.user.is_authenticated and request.is_ajax():
        response_data = {}
        ques_no = request.POST.get('question_no')
        i = request.POST.get('ip')
        i = str(i)
        ans = subprocess.Popen("data/standard/executable/question{}/a.out".format(ques_no),
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (out, err) = ans.communicate(input=i.encode())
        response_data["out"] = out.decode()

        return JsonResponse(response_data)


def result_page(request):
    if request.user.is_authenticated:
        if request.method == 'GET':
            questions = Question.objects.all()
            current_user = request.user.username
            current_score = request.user.profile.totalScore
            leaderboard = {}
            for profile in Profile.objects.order_by('-totalScore'):
                leaderboard[profile.user.username] = profile.totalScore
            rank = list(leaderboard.keys()).index(current_user)
            current_user_profile = Profile.objects.get(user=request.user)
            correct = current_user_profile.correctly_answered
            attempted = 0
            for question in questions:
                if Submissions.objects.filter(userID=request.user.id, quesID=question.pk).exists():
                    attempted += 1
            context = {'leaderboard' : leaderboard, 'username': current_user, 'rank': rank + 1, 'score': current_score,
                        'questions_solved': correct, 'questions_attempted': attempted}
            return render(request, 'Users/result rc.html', context)
    else:
        return HttpResponseRedirect(reverse("login"))

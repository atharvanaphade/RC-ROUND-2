from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10, default='')
    college = models.CharField(blank=True, max_length=255)
    totalScore = models.IntegerField(default=0)
    junior = models.BooleanField(default=True)
    correctly_answered = models.IntegerField(default=0)

    '''def __init__(self, user, phone, college, totalScore=0, junior=True, correctly_answered=0):
        self.user = user
        self.phone = phone
        self.college = college
        self.totalScore = totalScore
        self.junior = junior
        self.correctly_answered = correctly_answered
        directory = 'data/users_code/{}/'.format(self.user.username)
        #directory = self.user.username
        os.system('mkdir ' + directory)
        print('directory created!\n')'''

    def __str__(self):
        return self.user.username


class Question(models.Model):
    quesTitle = models.CharField(max_length=255)
    quesDesc = models.TextField(default="")
    sampleInput = models.TextField(default="")
    sampleOutput = models.TextField(default="")
    successfulAttempts = models.IntegerField(default=0)
    numberOfAttempts = models.IntegerField(default=0)
    score = models.IntegerField(default=0)

    def __str__(self):
        return self.quesTitle


class Submissions(models.Model):
    languages = [('c', 'C'), ('cpp', 'C++'), ('py', 'Python')]
    quesID = models.ForeignKey(Question, on_delete=models.CASCADE)  # as we are going to keep it as 1,2,3,4,5,6
    userID = models.ForeignKey(User, on_delete=models.CASCADE)
    language = models.CharField(max_length=3, choices=languages)
    code = models.TextField(max_length=10000000, default="")
    attempt = models.IntegerField(default=0)
    status = models.CharField(default='NA', max_length=5)
    submission_time = models.CharField(default="", max_length=15)
    score = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0)

    class Meta:
        verbose_name = 'Submissions'
        verbose_name_plural = 'Submissions'

    def __str__(self):
        return (self.userID.username + " - question-" + str(self.quesID.pk))

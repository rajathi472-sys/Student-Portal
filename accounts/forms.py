from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

class StudentLoginForm(forms.Form):
    roll_no = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)
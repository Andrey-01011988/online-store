from django import forms


class SwaggerUploadForm(forms.Form):
    swagger_file = forms.FileField()
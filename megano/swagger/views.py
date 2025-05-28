from django.shortcuts import render, redirect
from django.http import FileResponse, Http404
from .forms import SwaggerUploadForm
import os
from django.conf import settings

def upload_swagger(request):
    if request.method == 'POST':
        form = SwaggerUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Сохраняем файл с уникальным именем, например, в папке swagger_uploads
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'swagger_uploads')
            os.makedirs(upload_dir, exist_ok=True)
            uploaded_file = request.FILES['swagger_file']
            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            # Перенаправляем на страницу отображения Swagger UI, передавая имя файла
            return redirect('swagger:swagger-ui', filename=uploaded_file.name)
    else:
        form = SwaggerUploadForm()
    return render(request, 'swagger/upload_swagger.html', {'form': form})

def swagger_yaml_view(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, 'swagger_uploads', filename)
    if not os.path.exists(file_path):
        raise Http404("Swagger YAML файл не найден")
    return FileResponse(open(file_path, 'rb'), content_type='application/x-yaml')

def swagger_ui_view(request, filename):
    # Передаем в шаблон URL к swagger.yaml
    swagger_url = f"/swagger/yaml/{filename}/"
    return render(request, 'swagger/swagger-ui.html', {'swagger_url': swagger_url})

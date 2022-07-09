from django.shortcuts import render


def page_not_found(request, exception):
    """Отображение ошибки 404 - страница не существует."""
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def csrf_failure(request, reason=''):
    """Отображение ошибки проверки CSRF."""
    return render(
        request, 'core/403csrf.html', {'path': request.path}, status=403,
    )


def permission_denied(request, exception):
    """Отображение ошибки 403 - отказано в доступе."""
    return render(request, 'core/403.html', status=403)


def server_error(request):
    """Отображение ошибки 500 - ошибка сервера."""
    return render(request, 'core/500.html', status=500)

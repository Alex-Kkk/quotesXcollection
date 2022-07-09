from datetime import datetime


def year(request):
    """Контекст-процессор для передачи текущего года в шаблон."""
    return {
        'year': datetime.now().year,
    }

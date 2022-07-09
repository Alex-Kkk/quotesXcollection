from django.core.paginator import Paginator


def paginate(request, post_list, post_per_page):
    """Функция для разбития контента на страницы."""
    paginator = Paginator(post_list, post_per_page)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)

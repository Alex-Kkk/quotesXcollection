from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """Страница об авторе."""

    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Страница о использованных технологиях."""

    template_name = 'about/tech.html'

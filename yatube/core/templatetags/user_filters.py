from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    """Фильтр добавляющий CSS-класс к тегу шаблона."""
    return field.as_widget(attrs={'class': css})

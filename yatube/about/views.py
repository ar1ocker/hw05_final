from django.views.generic.base import TemplateView


class Author(TemplateView):
    template_name = 'about/author.html'


class Tech(TemplateView):
    template_name: str = 'about/tech.html'

from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/AboutAuthor.html'


class AboutTechView(TemplateView):
    template_name = 'about/AboutTech.html'

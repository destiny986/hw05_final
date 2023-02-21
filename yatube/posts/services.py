from django.core.paginator import Paginator
from django.conf import settings


def paging(request, list):
    paginator = Paginator(list, settings.MAX_POSTS_IN_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)

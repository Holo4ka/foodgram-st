from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination


class CustomLimitOffsetPagination(LimitOffsetPagination):
    # page_size = 10
    default_limit = 10
    
    def paginate_queryset(self, queryset, request, view=None):
        # Получаем параметры limit и offset из запроса
        limit = request.query_params.get(self.limit_query_param)
        offset = request.query_params.get(self.offset_query_param)

        # Проверяем, переданы ли оба параметра
        # if limit is None and offset is None:
            # return None  # Возвращаем None, чтобы отменить пагинацию

        # Если параметры переданы, продолжаем с обычной логикой пагинации
        return super().paginate_queryset(queryset, request, view)


class PageLimitPagination(PageNumberPagination):
    page_size = 10  # Значение по умолчанию
    page_query_param = 'page'
    page_size_query_param = 'limit'  # Позволяет задавать размер страницы через limit
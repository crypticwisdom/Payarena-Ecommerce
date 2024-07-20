from rest_framework.pagination import PageNumberPagination
from rest_framework.utils.urls import replace_query_param


class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'

    def get_next_link(self):
        if not self.page.has_next():
            return None
        page_number = self.page.next_page_number()
        return replace_query_param("", self.page_query_param, page_number)

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        page_number = self.page.previous_page_number()
        return replace_query_param("", self.page_query_param, page_number)



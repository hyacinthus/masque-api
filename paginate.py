import logging

from mongokit.cursor import Cursor
from mongokit.paginator import Paginator

from config import APIConfig

log = logging.getLogger("masque.paginate")


class Paginate:
    """ Provides pagination on a Cursor object

    Keyword arguments:
    cursor -- Cursor or List of a returned query
    page   -- The page number requested
    limit  -- The number of items per page
    """

    def __init__(self, cursor, page=1, limit=APIConfig.PAGESIZE):
        if isinstance(cursor, list):
            self.data = self.list_paging(cursor, page, limit)
        elif isinstance(cursor, Cursor):
            self.data = self.cursor_paging(cursor, page, limit)
        else:
            log.error("{} is neither list or Cursor type.".format(cursor))

    def list_paging(self, sorted_list, page, limit):
        """列表分页"""
        if len(sorted_list) == 0:
            # 页码为零, 返回 404
            return "", 404
        elif len(sorted_list) % limit != 0:
            num_pages = len(sorted_list) // limit + 1
        else:
            num_pages = len(sorted_list) // limit
        # 判断页码是否超出范围
        if page <= num_pages:
            return {
                "data": sorted_list[limit * (page - 1):limit * page],
                "paging": {
                    "num_pages": num_pages,
                    "current_page": page
                }
            }
        else:
            return {
                       "message": "page number out of range"
                   }, 400

    def cursor_paging(self, cursor, page, limit):
        """数据库分页"""
        paged_cursor = Paginator(cursor, page, limit)
        if paged_cursor.num_pages == 0:
            # 页码为零, 返回 404
            return "", 404
        elif page <= paged_cursor.num_pages:
            return {
                "data": [i for i in paged_cursor.items],
                "paging": {
                    "num_pages": paged_cursor.num_pages,
                    "current_page": paged_cursor.current_page
                }
            }
        else:
            return {
                       "message": "page number out of range"
                   }, 400

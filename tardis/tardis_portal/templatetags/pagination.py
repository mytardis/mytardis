from __future__ import unicode_literals

from django.template import Library
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = Library()

DOT = "."


@register.simple_tag
def paginator_number(data_list, paginator, page_num, query_string, page_index):
    """
    Generates an individual page index link in a paginated list.
    """
    if page_index == DOT:
        return mark_safe(
            '<li class=" page-item disabled"><a class="page-link" href="#">...</a></li> '
        )
    if page_index == page_num:
        return format_html(
            '<li class="page-item active"><span class="page-link">{}</span></li> ',
            page_index + 1,
        )
    return format_html(
        '<li class="page-item"><a class="page-link" href="{}"{}>{}</a></li> ',
        query_string.format(page=page_index),
        mark_safe(' class="end"' if page_index == paginator.num_pages - 1 else ""),
        page_index + 1,
    )


@register.inclusion_tag("tardis_portal/pagination.html")
def pagination(data_list, paginator, page_num, query_string):
    """
    Generates the series of links to the pages in a paginated list.
    """
    pagination_required = True
    if not pagination_required:
        page_range = []
    else:
        ON_EACH_SIDE = 3
        ON_ENDS = 2

        # If there are 10 or fewer pages, display links to every page.
        # Otherwise, do some fancy
        if paginator.num_pages <= 10:
            page_range = range(paginator.num_pages)
        else:
            # Insert "smart" pagination links, so that there are always ON_ENDS
            # links at either end of the list of pages, and there are always
            # ON_EACH_SIDE links at either end of the "current page" link.
            page_range = []
            if page_num > (ON_EACH_SIDE + ON_ENDS):
                page_range.extend(range(0, ON_ENDS))
                page_range.append(DOT)
                page_range.extend(range(page_num - ON_EACH_SIDE, page_num + 1))
            else:
                page_range.extend(range(0, page_num + 1))
            if page_num < (paginator.num_pages - ON_EACH_SIDE - ON_ENDS - 1):
                page_range.extend(range(page_num + 1, page_num + ON_EACH_SIDE + 1))
                page_range.append(DOT)
                page_range.extend(
                    range(paginator.num_pages - ON_ENDS, paginator.num_pages)
                )
            else:
                page_range.extend(range(page_num + 1, paginator.num_pages))

    return {
        "data_list": data_list,
        "paginator": paginator,
        "page_num": page_num,
        "query_string": query_string,
        "pagination_required": pagination_required,
        "page_range": page_range,
        "1": 1,
    }

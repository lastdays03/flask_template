"""Pagination utilities with HATEOAS support."""
from flask import request, url_for
from urllib.parse import urlencode


def generate_pagination_links(pagination, endpoint, **kwargs):
    """
    Generate pagination links (RFC 5988).

    Returns Link header with first, prev, next, last links.

    Args:
        pagination: SQLAlchemy pagination object
        endpoint: Flask endpoint name
        **kwargs: Additional URL parameters

    Returns:
        str: Link header value
    """
    links = []

    # Build query params
    params = {k: v for k, v in kwargs.items() if v is not None}

    # First page
    first_params = {**params, 'page': 1}
    links.append(f'<{_build_url(endpoint, **first_params)}>; rel="first"')

    # Previous page
    if pagination.has_prev:
        prev_params = {**params, 'page': pagination.prev_num}
        links.append(f'<{_build_url(endpoint, **prev_params)}>; rel="prev"')

    # Next page
    if pagination.has_next:
        next_params = {**params, 'page': pagination.next_num}
        links.append(f'<{_build_url(endpoint, **next_params)}>; rel="next"')

    # Last page
    last_params = {**params, 'page': pagination.pages}
    links.append(f'<{_build_url(endpoint, **last_params)}>; rel="last"')

    return ', '.join(links)


def _build_url(endpoint, **params):
    """Build URL with query parameters."""
    base_url = url_for(endpoint, _external=True)
    query_string = urlencode({k: v for k, v in params.items() if v is not None})
    return f'{base_url}?{query_string}' if query_string else base_url


def paginate_response(pagination, data, endpoint, **kwargs):
    """
    Create HATEOAS paginated response.

    Args:
        pagination: SQLAlchemy pagination object
        data: List of data items
        endpoint: Flask endpoint name
        **kwargs: Additional URL parameters

    Returns:
        dict: Paginated response with HATEOAS links
    """
    params = {k: v for k, v in kwargs.items() if v is not None}
    params['per_page'] = pagination.per_page

    return {
        'data': data,
        'meta': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        },
        'links': {
            'self': _build_url(endpoint, page=pagination.page, **params),
            'first': _build_url(endpoint, page=1, **params),
            'last': _build_url(endpoint, page=pagination.pages, **params),
            'next': _build_url(endpoint, page=pagination.next_num, **params) if pagination.has_next else None,
            'prev': _build_url(endpoint, page=pagination.prev_num, **params) if pagination.has_prev else None,
        }
    }


class Pagination:
    """Serializable pagination object for caching (detached from session)."""

    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total

    @property
    def pages(self):
        """Total number of pages."""
        if self.per_page == 0 or self.total == 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page

    @property
    def has_prev(self):
        """True if there is a previous page."""
        return self.page > 1

    @property
    def has_next(self):
        """True if there is a next page."""
        return self.page < self.pages

    @property
    def prev_num(self):
        """Previous page number."""
        return self.page - 1 if self.has_prev else None

    @property
    def next_num(self):
        """Next page number."""
        return self.page + 1 if self.has_next else None

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        """Iterate over pages (compatibility with SQLAlchemy Pagination)."""
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

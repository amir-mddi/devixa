from __future__ import annotations

from dealio.apps.common.dtos.http_error_dto import HttpErrorDTO


class FormHttpErrorResponseMixin:
    """Render infrastructure errors on the current form instead of returning JSON."""

    def handle_http_error_response(self, error: HttpErrorDTO):
        form = self.get_form()
        form.add_error(None, error.message)
        context = self.get_context_data(
            form=form,
            http_error=error,
        )
        return self.render_to_response(context, status=error.status_code)

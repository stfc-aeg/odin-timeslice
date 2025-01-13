import logging

from timeslice.base_adapter import BaseAdapter, ApiAdapterResponse, response_types
from timeslice.control import TimesliceError
from timeslice.control.controller import TimesliceController


class TimesliceControlAdapter(BaseAdapter):

    controller_cls = TimesliceController
    error_cls = TimesliceError

    @response_types('application/json', 'image/*', 'image/webp', default='application/json')
    def get(self, path, request):

        if path == "preview":
            return self.get_preview(request)

        return super().get(path, request)

    def get_preview(self, request):

        try:
            data = self.controller.get_preview_image()
            content_type = "image/jpeg"
            status_code = 200
        except self.error_cls as error:
            data = {"error": str(error)}
            content_type = "application/json"
            status_code = 400

        return ApiAdapterResponse(data, content_type=content_type, status_code=status_code)
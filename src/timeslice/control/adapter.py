import logging

from timeslice.base_adapter import BaseAdapter, ApiAdapterResponse, response_types
from timeslice.control import TimesliceError
from timeslice.control.controller import TimesliceController


class TimesliceControlAdapter(BaseAdapter):

    controller_cls = TimesliceController
    error_cls = TimesliceError

    @response_types(
        'application/json', 'image/*', 'image/webp', 'video/*', default='application/json'
    )
    def get(self, path, request):

        if path == "preview":
            response = self.get_preview()
        elif path == "preview_video":
            response = self.get_preview_video()
        else:
            response = super().get(path, request)

        return response

    def get_preview(self):

        try:
            data = self.controller.get_preview_image()
            content_type = "image/jpeg"
            status_code = 200
        except self.error_cls as error:
            data = {"error": str(error)}
            content_type = "application/json"
            status_code = 400

        return ApiAdapterResponse(data, content_type=content_type, status_code=status_code)

    def get_preview_video(self):

        try:
            data = self.controller.get_preview_video()
            content_type = "video/mp4"
            status_code = 200
        except self.error_cls as error:
            data = {"error": str(error)}
            content_type = "application/json"
            status_code = 400

        return ApiAdapterResponse(data, content_type=content_type, status_code=status_code)

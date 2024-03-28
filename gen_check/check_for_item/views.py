import base64
import io
import os
import uuid
from datetime import datetime

import pdfkit
import qrcode
from django.conf import settings
from django.http import FileResponse
from jinja2 import Template
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from gen_check.settings import PATH_TO_HTML_TO_PDF
from .models import Item
from .serialaizers import ItemSerializer


class CashMachineView(APIView):
    def __init__(self):
        super().__init__()
        self.app_folder = 'check_for_item'
        self.media_folder = 'media'
        self.template_folder = 'templates'
        self.template_f_name = 'check_template.html'
        self.path_for_app = os.path.join(settings.BASE_DIR, self.app_folder)
        self.templates_folder_path = os.path.join(self.path_for_app, self.template_folder)

    def qr_to_bytes(self):
        """
        Преобразование qr кода в байты для отправки по api
        :return:
        """
        qr_code_buffer = io.BytesIO()
        self.qr.save(qr_code_buffer)
        qr_code_base64 = base64.b64encode(qr_code_buffer.getvalue()).decode('utf-8')
        self.qr_code_base64 = qr_code_base64

    def generate_qr_code(self):
        """
        Генерация qr кода
        :return:
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"http://127.0.0.1:8000/media/{self.file_name.replace('.html', 'pdf___.pdf')}")
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(os.path.join(self.path_for_app, self.media_folder, f"{self.pdf_f_path.replace('.pdf', '.png')}"))
        self.qr = qr_img

    def conversion_html_to_pdf(self):
        """
        Конвертация html чека в pdf
        :return:
        """
        self.pdf_f_path = self.file_path.replace('.html', '') + 'pdf___.pdf'
        pdfkit_config = pdfkit.configuration(wkhtmltopdf=PATH_TO_HTML_TO_PDF)
        pdfkit.from_file(self.file_path, self.pdf_f_path,
                         configuration=pdfkit_config)

    def generate_unique_filename(self, file_extension='html'):
        """
        Генерация уникального имени файла на локальной машине.
        :param file_extension:
        :return:
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        unique_id = uuid.uuid4().hex
        self.file_name = f"{timestamp}_{unique_id}.{file_extension}"
        self.file_path = os.path.join(self.path_for_app, self.media_folder, self.file_name)

    def save_file(self):
        """
        Сохранение файла
        :return:
        """
        with open(self.file_path, 'w', encoding='utf-8') as file:
            file.write(self.rendered_template)

    def create_html_check(self):
        """
        Создание html чека на основании данных из БД
        :return:
        """
        with open(os.path.join(self.templates_folder_path, self.template_f_name), encoding='utf-8') as file:
            template_str = file.read()

        items = Item.objects.filter(id__in=self.context['item_ids'])
        serializer = ItemSerializer(items, many=True)
        total_amount = sum(item.price for item in items)

        self.context['items'] = serializer.data
        self.context['current_date'] = datetime.now().strftime('%d.%m.%y %H:%M')
        self.context['total_amount'] = total_amount

        template = Template(template_str)
        self.rendered_template = template.render(self.context)

    def post(self, request):
        """
        Обработка post запроса по адресу:
        api/v1/post/cash_machine
        Пример данных на вход:
        {
	        "items": [1, 2, 3]
        }
        Где список - список id товаров из модели Item
        :param request:
        :return:
        """
        item_ids = request.data.get('items', [])
        self.context = {'item_ids': item_ids}
        self.generate_unique_filename()

        self.create_html_check()
        self.save_file()
        self.conversion_html_to_pdf()
        self.generate_qr_code()

        return Response(
            {'qr_code': self.qr_code_base64}, status=status.HTTP_200_OK)


class DownloadFileView(APIView):

    def get(self, request, file_name):
        """
        Обработка get запроса по адресу: media/<str:file_name>/ (отправляется с qr-кода)

        :param request:
        :param file_name:
        :return:
        """
        file_path = os.path.join(settings.BASE_DIR, 'check_for_item', 'media', file_name)
        print(file_path)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                response = FileResponse(file.read())
                return response
        else:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

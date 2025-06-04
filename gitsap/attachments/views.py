import uuid
import mimetypes
from django.utils import timezone
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from gitsap.attachments.models import Attachment


class AttachmentPresignUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        filename = request.data.get("filename")
        if not filename:
            return Response(
                {"error": "Missing filename"}, status=status.HTTP_400_BAD_REQUEST
            )

        content_type = (
            request.data.get("content_type")
            or mimetypes.guess_type(filename)[0]
            or "application/octet-stream"
        )
        ext = filename.split(".")[-1]
        now = timezone.now()

        key = f"attachments/{now:%Y/%m/%d}/{uuid.uuid4()}.{ext}"

        presigned_url = settings.S3_CLIENT.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )

        attachment = Attachment.objects.create(
            file=key,
            filename=filename,
            content_type=content_type,
        )

        return Response(
            {
                "id": str(attachment.id),
                "upload_url": presigned_url,
                "key": key,
                "filename": filename,
                "content_type": content_type,
            },
            status=status.HTTP_201_CREATED,
        )

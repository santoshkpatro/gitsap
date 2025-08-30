from rest_framework.response import Response


def success_response(data=None, message="OK", status_code=200, meta=None):
    return Response(
        {
            "success": True,
            "message": message,
            "error_code": 0,
            "data": data or {},
            "meta": meta or {},
        },
        status=status_code,
    )


def error_response(
    message="Something went wrong",
    error_code=400,
    status_code=None,
    meta=None,
    errors=None,
):
    return Response(
        {
            "success": False,
            "message": message,
            "error_code": error_code,
            "errors": errors or {},
            "meta": meta or {},
        },
        status=status_code or error_code,
    )

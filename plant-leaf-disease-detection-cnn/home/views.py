from django.shortcuts import render, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from home.predictor import predict as predict_leaf, _ensure_backend


# Create your views here.
def index(request):
    context = {
        "variable":"this is sent"
    }
    return render(request, 'index.html',context)
    # return HttpResponse("This is homepage")

def about(request):
    return render(request, 'about.html')
    # return HttpResponse("This is aboutpage")

def services(request):
    return render(request, 'services.html')
    # return HttpResponse("This is services page")

def contact(request):
    return render(request, 'contact.html')
    # return HttpResponse("This is contact page")


@csrf_exempt
def predict(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only", "ready": _ensure_backend()}, status=405)
    if "leaf_image" not in request.FILES:
        return JsonResponse({"error": "no leaf_image uploaded", "ready": _ensure_backend()}, status=400)
    upload = request.FILES["leaf_image"]
    try:
        result = predict_leaf(upload.read())
    except RuntimeError as exc:
        return JsonResponse({"error": str(exc), "ready": False}, status=503)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({"error": str(exc), "ready": True}, status=500)
    result["ready"] = True
    return JsonResponse(result)
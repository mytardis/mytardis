from django.http import HttpResponse

def endpoint(request):
    return HttpResponse('<nothing/>', mimetype="text/xml")
class CheckContextMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        if not request.path.startswith(('/check-pyme/','/static/')):
            request.session.pop('check',None)
        response=self.get_response(request)
        if request.path.startswith('/check-pyme/'):
            response['Cache-Control']='no-store, private'
            response['Referrer-Policy']='same-origin'
        return response

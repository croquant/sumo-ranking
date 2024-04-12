from ninja import NinjaAPI

from rikishi.views import rikishi_router

ninja_api = NinjaAPI()


@ninja_api.get("/hello")
def hello(request):
    return "Hello !"


ninja_api.add_router("/rikishi/", rikishi_router)

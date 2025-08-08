from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse,JsonResponse

from blog.models import Articles
# Create your views here.


def index(request):
    artlist = Articles.objects.all()
    context = {"articles_list":artlist}
    return render(request,"blog/index.html",context)

# @params user_id 应该由session 或 jwt 校验后获取
def detail(request,article_id,user_id):
    #TODO 读取缓存
    article = get_object_or_404(Articles, pk=article_id)
    return render(request, "blog/detail.html", {"article": article})

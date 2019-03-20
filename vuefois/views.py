from django.shortcuts import render, get_object_or_404
from .models import Video


def ranking(request):
    videos = Video.objects.all().order_by('-view_count')[:100]
    return render(request, 'vuefois/ranking.html', {'videos': videos})

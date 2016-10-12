from django.shortcuts import render, get_object_or_404

from .models import Diff

#FIXME: protect
def diff_detail(request, pk):
    diff = get_object_or_404(Diff, pk=pk)

    return render(request, 'osmdata/adiff/diff_detail.xml', {
        'diff': diff
    }, content_type='text/xml')

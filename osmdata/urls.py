from django.conf.urls import url

from .views import diff_detail

urlpatterns = [
    url(r'^diff/(?P<pk>\d+)', diff_detail, name='diff_detail'),
]

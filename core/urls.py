from django.conf.urls import patterns, url

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'core.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', 'core.views.index'),
    url(r'^api/station/register$', 'account.views.register'),
    url(r'^api/station/ping$', 'account.views.ping'),
    url(r'^api/authenticate$', 'core.views.authenticate'),
    url(r'^api/confirm$', 'core.views.confirm'),
    url(r'^api/report$', 'core.views.report'),
    url(r'^api/complete$', 'core.views.complete', name='callback'),
)

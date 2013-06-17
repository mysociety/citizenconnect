from ratelimitbackend.backends import RateLimitModelBackend

class RateLimitedBackend(RateLimitModelBackend):
    minutes = 60
    requests = 3

    def key(self, request, dt):
        return '%s%s-%s' % (
            self.cache_prefix,
            request.POST['username'],
            dt.strftime('%Y%m%d%H%M'),
        )

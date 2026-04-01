from rest_framework.throttling import UserRateThrottle

class IPPeerRateThrottle(UserRateThrottle):
    """
    IP-based rate throttle for additional protection against IP spoofing.
    Gets the real IP from X-Forwarded-For header.
    """
    scope = 'ip'
    
    def get_ident(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


class SensitiveAPIThrottle(UserRateThrottle):
    """
    Stricter throttle for sensitive APIs like approvals, finance, admin.
    """
    scope = '敏感API'

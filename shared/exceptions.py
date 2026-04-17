# Exceptions métier typées
# Utilisées dans les services, converties en HTTP par main.py

class NotFoundError(LookupError):
    """Entité introuvable → HTTP 404"""
    pass


class BusinessRuleError(ValueError):
    """Règle métier violée → HTTP 400"""
    pass


class ForbiddenError(PermissionError):
    """Accès non autorisé → HTTP 403"""
    pass

def user_context(request):
    """Добавляет пользователя в контекст всех шаблонов"""
    return {
        'user': {
            'id': request.session.get('user_id'),
            'email': request.session.get('user_email'),
            'name': request.session.get('user_name'),
            'is_authenticated': request.session.get('user_id') is not None,
        }
    }
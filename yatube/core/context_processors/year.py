import datetime as dt


def year(request):
    """Добавляет в контекст переменную year"""
    return {
        'year': dt.date.today().year
    }

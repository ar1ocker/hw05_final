from datetime import datetime


def year(requests):
    '''Добавление переменной с текущим годом'''

    return {
        'year': datetime.now().year
    }

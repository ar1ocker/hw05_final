from http import HTTPStatus


"""
Стоит наверное пояснить работу текущих тестов и возможно
облегчить работу ревьюера

Тут я использую самописный класс Url для формализации основных свойств
адреса, а именно:
 - Каким кодом отвечает адрес для разных категорий пользователей
 - Каким шаблоном
 - С каким контекстом

В теории - это позволит в будующем не бегать по всем тестам из-за изменения
части кода приложения, а поправить лишь список с Url

Для описания контекста в настоящий момент использую несколько дополнительных
классов которые имеют переопределенный метод __eq__:
IndividualField - для сравнения с простыми частями контекста: числами,
    строками, bool и т.д., в общем всё, что можно сравнить напрямую

IndividualObject - для сравнения со сложными объектами,
    тип сравниваемого объекта - не важен,
    если поля имеют одинаковое название и одинаковое значение
    значит IndividualObject == часть контекста
    P.s.: Важно сравнивать именно IndividualObject с другим объектом
    Ибо IndividualObject имеет нестандартный __eq__
    (по хорошему надо вообще делать сравнение в отдельном методе,
    а не с помощью ==, но с == нативно работает библиотека unittest)

ObjectsInList - проверяет, что в части контекста есть все объекты из
    списка objects_in

IterableWithLen - для сравнения с иттерируемыми объектами (пагинаторы),
    если часть контекста имеет такую же длинну
    IterableWithLen == часть контекста

Form - для сравнения с формами.
    Часть контекста в виде формы должна обладать задаными полями и
    иметь одинаковый тип, для того, чтобы сравнение
    Form и части контекста дало True
    Пример:

    Url(reverse('posts:post_create'),
        default_template='posts/create_post.html',
        help_text='Страница создания поста',
        context=Form('form',
                     text=forms.fields.CharField,
                     group=forms.fields.ChoiceField))
"""


class ReprMixin():
    """
    Класс который определяет отображение потомков
    Нужно для вывода в консоль при использовании subTest()
    """
    def __repr__(self):
        params_text = ''
        for key, value in self.__dict__.items():
            if value is not None and key != 'help_text' and value != {}:
                params_text += f'{key}: {value}\n'

        return (f'{self.__class__.__name__} - {self.help_text} -'
                f' Параметры:\n{params_text}')

    def __str__(self):
        return self.__repr__()


class Url(ReprMixin):
    """
    Класс предназначен для удобного представления url адреса со всеми
    возможными сценариями для каждой категории юзеров
    (гость, авторизованный, автор)

    Позволяет подробно указывать в ошибках на какой конкретно странице
    и с какими параметрами не проходят тесты
    Также даёт возможность централизованно хранить все страницы в тесте
    с их параметрами, доступом и контекстом
    """
    def __init__(self,
                 url: str,
                 *,
                 guest_template: str = None,
                 authorized_template: str = None,
                 author_template: str = None,
                 guest_status: HTTPStatus = None,
                 authorized_status: HTTPStatus = None,
                 author_status: HTTPStatus = None,

                 default_template: str = None,
                 default_status: HTTPStatus = None,

                 post_data: dict = {},
                 context: object = None,
                 help_text: str = ''):

        self.url = url

        self.guest_template = guest_template
        self.authorized_template = authorized_template
        self.author_template = author_template
        self.guest_status = guest_status
        self.authorized_status = authorized_status
        self.author_status = author_status
        self.post_data = post_data
        # Сахар, чтобы при наличии всего 1 объекта контекста
        # не оформлять его в list
        if isinstance(context, list):
            self.context = context
        else:
            self.context = [context]

        self.help_text = help_text

        # Если default аргументы заданы - переопределяем
        # то, что в настоящий момент None
        self.guest_template = guest_template or default_template
        self.authorized_template = authorized_template or default_template
        self.author_template = author_template or default_template

        self.guest_status = guest_status or default_status
        self.authorized_status = authorized_status or default_status
        self.author_status = author_status or default_status


class IndividualField(ReprMixin):
    """
    Часть контекста в виде поля с простым объектом
    (который можно сравнить напрямую не прибегая
    к древним колдунствам с __eq__)
    """
    def __init__(self,
                 context_name: str,
                 value,
                 help_text: str = ''):

        self.context_name = context_name
        self.value = value
        self.help_text = help_text

    def __eq__(self, other):
        return self.value == other


class IndividualObject(ReprMixin):
    """
    Часть контекста с объектом имеющим определенные поля
    Сравнение идёт по полям

    Стоит учесть, что при наличии ForeignField в модели которая
    передается в контекст в сам контекст попадает только id, а не весь объект
    Например:
    Если в контекст передалась модель post с ForeignField(author)
    в сам контекст страницы попадёт только поле author_id
    """
    def __init__(self,
                 context_name: str,
                 help_text: str = '',
                 **fields):

        self.context_name = context_name
        self.fields = fields
        self.help_text = help_text

    def __eq__(self, other):
        for key, value in self.fields.items():
            try:
                if other.__dict__.get(key) != value:
                    return False
            except KeyError:
                return False

        return True


class Form(ReprMixin):
    """
    Часть контекста которая является формой
    Form('form',
         text=forms.fields.CharField,
         group=forms.fields.ChoiceField)
    """
    def __init__(self,
                 context_name: str,
                 help_text: str = '',
                 **fields):

        self.context_name = context_name
        self.fields = fields
        self.help_text = help_text

    def __eq__(self, other):
        """
        Получение всех полей в форме и сравнение типов полей
        + проверка наличия
        """
        for key, value in self.fields.items():
            try:
                if not isinstance(other.fields.get(key), value):
                    return False
            except KeyError:
                return False

        return True


class ObjectsInList(ReprMixin):
    """
    Часть контекста (список), в котором есть определенные
    объекты

    Сравнение с ObjectsInList даст True только в том случае,
    если в сравниваемом списке есть ВСЕ объекты из параметра objects_in
    Пример:
    lst = ['a', 15, 'test', 'abrakadabra']
    tester = ObjectsInList('', objects_in=['a', 15])
    (tester == lst) == True
    """
    def __init__(self,
                 context_name: str,
                 objects_in: object,
                 help_text: str = ''):

        self.context_name = context_name
        self.help_text = help_text

        # Сахар, позволяющий передавать в objects_in просто одиночный объект
        # с последующим его преобразованием в list
        if isinstance(objects_in, list):
            self.objects_in = objects_in
        elif objects_in:
            self.objects_in = [objects_in]
        else:
            raise ValueError('objects_in не должен быть None')

    def all_objects_in_list(self, other_list) -> bool:
        for self_obj in self.objects_in:
            found = False
            for other_obj in other_list:
                if self_obj == other_obj:
                    found = True

            if not found:
                return False

        return True

    def __eq__(self, others):
        return self.all_objects_in_list(others)


class IterableWithLen(ReprMixin):
    """
    Для проверки сравниваемых списков на количество объектов
    """
    def __init__(self,
                 context_name: str,
                 context_length: int,
                 help_text: str = ''):

        self.context_name = context_name
        self.context_length = context_length
        self.help_text = help_text

    def __eq__(self, other):
        return len(other) == self.context_length

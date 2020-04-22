import pathlib


class PostModel:
    __FRONT_MATTER = '+++'
    __FM_ASSIGNMENT = '='

    def __init__(self):
        self.title = None
        self.author = None
        self.date = None
        self.slug = None
        self.category = None
        self.tags = None
        self.labels = []
        self.formats = []
        self.player = None
        self.image = None
        self.content = None
        self.original_content = None
        self.raw_meta = None
        self.links = []

    def dumps(self, abs_file_name):
        _s = '{0}\n'.format(self.__FRONT_MATTER)
        for key in self.__dict__.keys():
            if not key == 'content' and not key == 'original_content' and not key == 'raw_meta':
                if self.__dict__.get(key):
                    _s += self.build_yaml_attribute(key)
        _s += 'legacy = true\n'
        _s += '{0}\n'.format(self.__FRONT_MATTER)
        _s += '\n'
        _s += '{0}\n'.format(self.translate_content())
        _s += self.add_sanitized_raw_meta()
        #print(_s)

        with open(abs_file_name, 'w') as f:
            f.write(_s)

    def translate_content(self):
        return self.content.replace('https://necroslaughter.de/wp-content/uploads', 'images/').replace('http://necroslaughter.de/wp-content/uploads', 'images/')

    def build_yaml_attribute(self, key):
        _TEMPLATE_ = '{} {} {}\n'
        return _TEMPLATE_.format(
            key,
            self.__FM_ASSIGNMENT,
            self.translate_attribute_value_to_yaml_safe(key)
        )

    def translate_attribute_value_to_yaml_safe(self, key):
        value = self.__dict__.get(key)
        if isinstance(value, str):
            return '"{}"'.format(value.replace('\"', '\\"').replace('https://necroslaughter.de/wp-content/uploads/', 'images/').replace('http://necroslaughter.de/wp-content/uploads', 'images/'))
        if isinstance(value, list):
            _s = '['
            for i in value:
                _s += '"{}", '.format(i.replace('"', '\\"'))
            _s += ']'
            return _s
        return '"{}"'.format(str(value).replace('"', '\\"'))

    def add_sanitized_raw_meta(self):
        if self.raw_meta is None:
            return ''
        else:
            _s = ''
            for l in self.raw_meta.splitlines():
                if l in self.links:
                    pass
                else:
                    _s += '{0} / \n'.format(l)
            if _s:
                return '\n---\n**Infos:**\n' + _s
            else:
                return ''

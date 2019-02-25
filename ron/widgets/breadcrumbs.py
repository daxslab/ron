from ron.base import Widget
from yatl.helpers import OL, A, LI
from ron import request


class Breadcrumbs(Widget):

    def run(self):
        items = []

        item_options = self.options.pop('item_options', {})

        for item in self.options['items']:
            if not isinstance(item, dict):
                raise AttributeError

            this_item_options = item_options
            if request.path == item['url']:
                this_item_options['_class'] += ' active'

            items.append(LI(A(item['label'], _href=item['url']), **this_item_options))

        return OL(*items, _class='breadcrumbs').xml()

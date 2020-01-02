import re
from bottle import Router

from ron.base.ronobject import RonObject
from ron.exceptions.invalid_configuration_exception import InvalidConfigurationException

class UrlManagerComponent(RonObject):

    rules = []

    remove_rules = []

    def set_routes(self):
        from ron import Application
        for route in self.rules:
            try:
                bottle_route = [route[0], route[1], Application().find_action(route[2])]
                Application().route(*bottle_route)
            except:
                raise InvalidConfigurationException()

    def remove_defined_routes(self):
        from ron import Application
        current_routes = [r for r in Application().routes]

        for default_route in Application().routes:
            for rule_to_remove in self.remove_rules:
                try:
                    if isinstance(rule_to_remove, str):
                        rule = rule_to_remove
                        method = '*'
                    else:
                        rule = rule_to_remove[0]
                        if isinstance(rule_to_remove[1], str) and rule_to_remove[1] != '*':
                            method = [rule_to_remove[1]]
                        else:
                            method = rule_to_remove[1]
                except:
                    raise InvalidConfigurationException()
                if re.findall(rule, default_route.rule) and (method == '*' or default_route.method in method):
                    if default_route in current_routes:
                        current_routes.remove(default_route)

        if current_routes:
            Application().router = Router()
            Application().routes = []
            for route in current_routes:
                Application().add_route(route)

from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import prompt
import pathlib
import json

CONFIG_FILE = pathlib.Path.cwd() / "config.json"


class NumberValidator(Validator):
    def validate(self, document):
        text = document.text

        if text and not text.isdigit():
            i = 0

            for i, c in enumerate(text):
                if not c.isdigit():
                    break

            raise ValidationError(message='This input contains non-numeric characters', cursor_position=i)


def main():
    config = {}

    domain = prompt("Domain of the website or AWS API Gateway [default: masothue.com]: ")
    if domain == "":
        domain = "masothue.com"
    config["domain"] = domain

    rate_limit = prompt("Maximum requests per second [default: 8]: ", validator=NumberValidator())
    if rate_limit == "":
        rate_limit = 8
    config["rate_limit"] = int(rate_limit)

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


if __name__ == "__main__":
    main()

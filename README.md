# Ron - A Funny and Drinkable Python Web Framework from a Bottle

Ron is an experimental Python web framework built on top of the Bottle framework. It aims to provide a fun and enjoyable learning experience for developers interested in web development with Python.

## Features

- Lightweight and easy-to-use.
- Utilizes the simplicity and flexibility of the Bottle framework.
- Designed to be easily understandable for beginners.
- Provides a range of built-in functionalities for rapid development.

## Installation

To install Ron, you can use pip:

```bash
pip install -e git+https://github.com/daxslab/ron.git#egg=ron
```

## Run the Ron development server:
```python
from ron import debug, run, Application

if __name__ == '__main__':
    debug(True)
    app = Application({})
    run(app, reloader=True, host='127.0.0.1', port=8080)
```

## Contributing
We welcome contributions to the Ron project! If you encounter any issues or have suggestions for improvements, please feel free to open an issue or submit a pull request on the Ron GitHub repository.

## License
Ron is released under the MIT License. See LICENSE for more details.

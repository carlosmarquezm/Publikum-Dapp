from flask import Flask
from main import main as main_blueprint

app = Flask(__name__)

# Register the main blueprint
app.register_blueprint(main_blueprint)


@app.route('/')
def hello_world():
    return 'Hello, World!'


if __name__ == '__main__':
    app.run()

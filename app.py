from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return {'message': 'Welcome to Game of Thrones API'}

if __name__ == '__main__':
    app.run(debug=True)

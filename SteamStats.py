from flask import Flask, request, redirect, render_template, abort

app = Flask(__name__)
app.config.update({
    'SESSION_PERMANENT': True,
    'PERMANENT_SESSION_LIFETIME': 2592000,
    'DEBUG': True
})

@app.route('/')
def index():
    return render_template('index.jinja2')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.jinja2'), 404
    
@app.route('/login')
def login():
    return render_template('login.jinja2')

if __name__ == '__main__':
    app.run()
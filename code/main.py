from flask import Flask
from apiendpoints import app as endpoints_app

app = Flask(__name__)

# Registering endpoints from endpoints.py
app.register_blueprint(endpoints_app)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

from flask import Flask, render_template, url_for, redirect

from routes.customfields import fields
from routes.auth import auth, get_access_token

app = Flask(__name__)

app.register_blueprint(fields)
app.register_blueprint(auth)

@app.route('/')
def index():
    access_token = get_access_token()
    
    if not access_token:
        # Redirect to a token upload page if no access token is found
        return redirect(url_for('auth.upload_token'))
    
    # Render the template without preloading items and item sets
    return render_template('field_management.html')

if __name__ == '__main__':

    app.run(debug=True)

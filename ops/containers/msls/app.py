import os
import base64
import csv

from flask import redirect, request, render_template, jsonify, make_response, Flask
from flask_wtf.csrf import CSRFProtect
from urllib.parse import urlencode

app = Flask(__name__)

csrf = CSRFProtect()
csrf.init_app(app)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

signed_in = True

ENCODE_NAME = 'ascii'

ID_FIELD = 'id'
USERNAME_FIELD = 'username'
NAME_FIELD = 'name'
EMAIL_FIELD = 'email'
FIRST_NAME_FIELD = 'first_name'
LAST_NAME_FIELD = 'last_name'
HICN_FIELD = 'hicn'
MBI_FIELD = 'mbi'
CODE_KEY = 'code'
AUTH_HEADER = 'Authorization'


def _base64_encode(string):
    encoded = base64.urlsafe_b64encode(string)
    return encoded.rstrip(b'=')


def _base64_decode(string):
    padding = 4 - (len(string) % 4)
    string = string + ('=' * padding)
    return base64.urlsafe_b64decode(string)


def _encode(usr='', name='', first_name='', last_name='', email='', hicn='', mbi=''):
    return '{}.{}.{}.{}.{}.{}.{}'.format(
        _base64_encode(usr.encode(ENCODE_NAME)).decode(ENCODE_NAME),
        _base64_encode(name.encode(ENCODE_NAME)).decode(ENCODE_NAME),
        _base64_encode(first_name.encode(ENCODE_NAME)).decode(ENCODE_NAME),
        _base64_encode(last_name.encode(ENCODE_NAME)).decode(ENCODE_NAME),
        _base64_encode(email.encode(ENCODE_NAME)).decode(ENCODE_NAME),
        _base64_encode(hicn.encode(ENCODE_NAME)).decode(ENCODE_NAME),
        _base64_encode(mbi.encode(ENCODE_NAME)).decode(ENCODE_NAME)
    )


def _decode(b64code):
    flds = b64code.split('.')
    return {
        'usr': _base64_decode(flds[0]).decode(ENCODE_NAME),
        'name': _base64_decode(flds[1]).decode(ENCODE_NAME),
        'first_name': _base64_decode(flds[2]).decode(ENCODE_NAME),
        'last_name': _base64_decode(flds[3]).decode(ENCODE_NAME),
        'email': _base64_decode(flds[4]).decode(ENCODE_NAME),
        'hicn': _base64_decode(flds[5]).decode(ENCODE_NAME),
        'mbi': _base64_decode(flds[6]).decode(ENCODE_NAME),
    }


def _load_user_data():
    csv_path = os.path.join(os.path.dirname(__file__), 'files', 'users.csv')
    users = []

    if os.path.exists(csv_path):
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    users.append({
                        'username': row.get('username', '').strip(),
                        'hicn': row.get('hicn', '').strip(),
                        'mbi': row.get('mbi', '').strip(),
                        'name': row.get('name', '').strip(),
                        'first_name': row.get('first_name', '').strip(),
                        'last_name': row.get('last_name', '').strip(),
                        'email': row.get('email', '').strip()
                    })
        except Exception as e:
            print(f"Error loading CSV: {e}")

    return users


@app.route('/sso/authorize', methods=['GET'])
def login_page():
    relay = request.args.get('relay', 'missing')
    redirect_uri = request.args.get('redirect_uri', 'missing')
    users = _load_user_data()
    return render_template('login.html', relay=relay, redirect_uri=redirect_uri, users=users)


@app.route('/login/', methods=['POST'])
def login():
    redirect_url = request.form.get('redirect_uri', None)

    req_token = _encode(
        request.form.get(USERNAME_FIELD, ''),
        request.form.get(NAME_FIELD, ''),
        request.form.get(FIRST_NAME_FIELD, ''),
        request.form.get(LAST_NAME_FIELD, ''),
        request.form.get(EMAIL_FIELD, ''),
        request.form.get(HICN_FIELD, ''),
        request.form.get(MBI_FIELD, '')
    )

    qparams = {
        'req_token': req_token,
        'relay': request.form.get('relay', '')
    }

    print('redirect={}?{}'.format(redirect_url, urlencode(qparams)))
    return redirect('{}?{}'.format(redirect_url, urlencode(qparams)))


@app.route('/health', methods=['GET'])
def health():
    return make_response(jsonify({'message': "all's well"}))


@csrf.exempt
@app.route('/sso/session', methods=['POST'])
def token():
    request_token = request.json.get('request_token', None)

    if request_token is None:
        return make_response(jsonify({'message': 'Bad Request, missing request token.'}), 400)

    user_info = _decode(request_token)

    token = {
        'user_id': user_info['usr'],
        'auth_token': request_token,
    }

    return make_response(jsonify(token))


@app.route('/v1/users/<usr>', methods=['GET'])
def userinfo(usr):

    global signed_in

    if signed_in is True:
        tkn = request.headers.get(AUTH_HEADER, None)
        if tkn is None:
            return make_response(jsonify({"message": "Bad Request, missing request token."}), 400)
        if not tkn.startswith("Bearer "):
            return make_response(jsonify({"message": "Bad Request, malformed bearer token."}), 400)
        tkn = tkn.split()[1]
        user_info = _decode(tkn)
        slsx_userinfo = {
            "data": {
                "user": {
                    "id": user_info["usr"],
                    "username": user_info["name"],
                    "email": user_info["email"],
                    "firstName": user_info["first_name"],
                    "lastName": user_info["last_name"],
                    "hicn": user_info["hicn"],
                    "mbi": user_info["mbi"],
                },
            },
        }
        signed_in = False
        return make_response(jsonify(slsx_userinfo))
    else:
        signed_in = True
        return make_response(jsonify({"message": "not signed in."}), 403)


@app.route('/sso/signout', methods=['GET'])
def signout():
    return make_response(jsonify({'message': 'signed out.'}), 302)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

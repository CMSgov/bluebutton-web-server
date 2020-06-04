package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
)

/*
	accept regular endpoints and return sain responses
	match usernames and passwords, but as plain text
	1. login screen
	2. redirect with code
	3. accept code post
	4. return token
	5. return info on userinfo endpoint


MEDICARE_LOGIN_URI = env('DJANGO_MEDICARE_LOGIN_URI',
                         'https://dev2.account.mymedicare.gov/?scope=openid%20profile&client_id=bluebutton')
MEDICARE_REDIRECT_URI = env(
    'DJANGO_MEDICARE_REDIRECT_URI', 'http://localhost:8000/mymedicare/sls-callback')
SLS_USERINFO_ENDPOINT = env(
    'DJANGO_SLS_USERINFO_ENDPOINT', 'https://dev.accounts.cms.gov/v1/oauth/userinfo')
SLS_TOKEN_ENDPOINT = env(
    'DJANGO_SLS_TOKEN_ENDPOINT', 'https://dev.accounts.cms.gov/v1/oauth/token')
*/

const (
	USERNAME_FIELD    = "username"
	NAME_FIELD        = "name"
	GIVEN_NAME_FIELD  = "given_name"
	FAMILY_NAME_FIELD = "family_name"
	EMAIL_FIELD       = "email"
	IDENTITY_FIELD    = "pt_identity"
	IDENTITY_TYPE     = "identity_type"
	CODE_KEY          = "code"
	AUTH_HEADER       = "Authorization"
	BENE_IDENTITY     = "beneficiary_identity"
)

func logRequest(w http.Handler) http.Handler {
	return http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		v, err := httputil.DumpRequest(r, true)
		log.Printf("%q : %s", v, err)
		w.ServeHTTP(rw, r)
	})
}

func main() {
	t := template.Must(template.New("loginpage").Parse(login_template))
	http.Handle("/", logRequest(presentLogin(t)))

	http.Handle("/login", logRequest(http.HandlerFunc(handleLogin)))
	http.Handle("/token", logRequest(http.HandlerFunc(handleCode)))
	http.Handle("/userinfo", logRequest(http.HandlerFunc(handleUserinfo)))
	http.ListenAndServe(":8080", nil)
}

func handleCode(rw http.ResponseWriter, r *http.Request) {
	body := &struct {
		Code string `json:"code"`
	}{}

	// Try to decode the request body into the struct. If there is an error,
	// respond to the client with the error message and a 400 status code.
	err := json.NewDecoder(r.Body).Decode(body)
	if err != nil {
		http.Error(rw, err.Error(), http.StatusBadRequest)
		return
	}

	token := map[string]string{
		"access_token": body.Code,
	}

	log.Println(token)
	rw.Header().Set("Content-Type", "application/json")
	json.NewEncoder(rw).Encode(token)
}

func handleUserinfo(rw http.ResponseWriter, r *http.Request) {
	tkn := code(strings.Split(r.Header.Get(AUTH_HEADER), " ")[1])
	json.NewEncoder(rw).Encode(tkn.userinfo())
}

func presentLogin(t *template.Template) http.Handler {
	return http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		rw.Header().Set("Content-Type", "text/html; charset=utf-8")
		r.ParseForm()
		t.Execute(rw, r.Form)
	})
}

func handleLogin(rw http.ResponseWriter, r *http.Request) {
	code := login(r)
	// redirect with the state, and code
	u, err := url.Parse(r.FormValue("redirect_uri"))
	if err != nil {
		http.Error(rw, err.Error(), http.StatusInternalServerError)
		return
	}

	q := u.Query()
	q.Add("code", string(code))
	q.Add("state", r.FormValue("state"))

	u.RawQuery = q.Encode()

	http.Redirect(rw, r, u.String(), http.StatusFound)
}

func login(r *http.Request) code {
	usr := r.FormValue(USERNAME_FIELD)
	name := r.FormValue(NAME_FIELD)
	given_name := r.FormValue(GIVEN_NAME_FIELD)
	family_name := r.FormValue(FAMILY_NAME_FIELD)
	email := r.FormValue(EMAIL_FIELD)
	pt_identity := r.FormValue(IDENTITY_FIELD)
	identity_type := r.FormValue(BENE_IDENTITY)

	return encode(usr, name, given_name, family_name, email, pt_identity, identity_type)
}

type code string

func (c code) userinfo() *userinfo {
	usr, name, given_name, family_name, email, pt_identity, identity_type := decode(string(c))
	return &userinfo{
		Sub:  usr,
		Name: name,
		Given_name: given_name,
		Family_name: family_name,
		Email: email,
		Pt_identity: pt_identity,
		Identity_type: identity_type,
	}
}

func decode(c string) (string, string, string, string, string, string, string) {
	d_usr, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[0])
	d_name, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[1])
	d_given_name, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[2])
	d_family_name, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[3])
	d_email, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[4])
	d_pt_identity, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[5])
	d_identity_type, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[6])
	return string(d_usr), string(d_name), string(d_given_name), string(d_family_name),
	       string(d_email), string(d_pt_identity), string(d_identity_type)
}

func encode(usr,name, given_name, family_name, email, pt_identity, identity_type string) code {
	e_usr := base64.RawURLEncoding.EncodeToString([]byte(usr))
	e_name := base64.RawURLEncoding.EncodeToString([]byte(name))
	e_given_name := base64.RawURLEncoding.EncodeToString([]byte(given_name))
	e_family_name := base64.RawURLEncoding.EncodeToString([]byte(family_name))
	e_email := base64.RawURLEncoding.EncodeToString([]byte(email))
	e_pt_identity := base64.RawURLEncoding.EncodeToString([]byte(pt_identity))
	e_identity_type := base64.RawURLEncoding.EncodeToString([]byte(identity_type))
	return code(fmt.Sprintf("%s.%s.%s.%s.%s.%s.%s", e_usr, e_name, e_given_name,
                    e_family_name, e_email, e_pt_identity, e_identity_type))
}

type userinfo struct {
	Sub         	string `json:"sub"`
	Name        	string `json:"name"`
	Given_name  	string `json:"given_name"`
	Family_name 	string `json:"family_name"`
	Email       	string `json:"email"`
	Pt_identity 	string `json:"pt_identity"`
	Identity_type	string `json:"identity_type"`
}

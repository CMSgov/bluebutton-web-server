package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	// "io/ioutil"
	"os"
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

MEDICARE_SLSX_LOGIN_URI=env('DJANGO_MEDICARE_SLSX_LOGIN_URI',
							'https://test.medicare.gov/sso/authorize?client_id=bb2api')
MEDICARE_SLSX_REDIRECT_URI=env('DJANGO_MEDICARE_SLSX_REDIRECT_URI',
							   'http://localhost:8000/mymedicare/sls-callback')
SLSX_USERINFO_ENDPOINT=env('DJANGO_SLSX_USERINFO_ENDPOINT', 'https://test.accounts.cms.gov/v1/users')
SLSX_TOKEN_ENDPOINT=env('DJANGO_SLSX_TOKEN_ENDPOINT', 'https://test.medicare.gov/sso/session')

SLSX exchange for auth_token:

{
"auth_token":"6yemAjHlDCa15RxXXNr15hfd/Q6Uvcc11KbgXhp/AgrJ",
"role":"consumer",
"user_id":"0854b569-5d28-4aa7-9878-fccdb15b4ffc",
"session_id":"36106cbd6982479c8c1dce52d8fb1588"}'


Sample SLSX response:

{
 "status": "ok",
 "code": 200,
 "data": {
   "user": {
     "id": "0854b569-5d28-4aa7-9878-fccdb15b4ffc",
     "username": "BbUser10000",
     "email": null,
     "firstName": null,
     "middleName": null,
     "lastName": null,
     "suffix": null,
     "dateOfBirth": null,
     "ssn": null,
     "city": null,
     "state": null,
     "addressLine1": null,
     "addressLine2": null,
     "zipcode": null,
     "zipcodeExtension": null,
     "phoneNumber": null,
     "challenges": null,
     "webBrokerInfo": null,
     "isManuallyDisabled": false,
     "requiresConfirm": null,
     "loa": 0,
     "loaAdminReason": null,
     "lastLoginTime": 1617920826,
     "createdTime": 1594071993,
     "updatedTime": 1617920826,
     "hicn": "1000087197",
     "passwordExpirationTime": 1680992826,
     "isDisabled": false,
     "customUserInfo": {
       "mbi": "2S17E00AA00"
     },
     "mbi": "2S17E00AA00"
   }
 }
 }


	*/

const (
	ID_FIELD          	= "id"
	USERNAME_FIELD    	= "username"
	NAME_FIELD    		= "name"
	EMAIL_FIELD       	= "email"
	FIRST_NAME_FIELD  	= "fisrt_name"
	LAST_NAME_FIELD   	= "last_name"
	HICN_FIELD        = "hicn"
	MBI_FIELD         = "mbi"
	CODE_KEY          = "code"
	AUTH_HEADER       = "Authorization"
)

type LoginPageData struct {
    HelpMessage string
	Relay       string
	Redirect_uri    string
	MbiValues   []string
	HicnValues  []string
}

func logRequest(w http.Handler) http.Handler {
	return http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		v, err := httputil.DumpRequest(r, true)
		log.Printf("%q : %s", v, err)
		w.ServeHTTP(rw, r)
	})
}

var mbi_list = os.Getenv("SAMPLE_MBI_LIST")
var hicn_list = os.Getenv("SAMPLE_HICN_LIST")
var fhir_id_list = os.Getenv("SAMPLE_FHIR_ID_LIST")
var mbi_array = strings.Split(mbi_list, ",")
var hicn_array = strings.Split(hicn_list, ",")
var fhir_id_array = strings.Split(fhir_id_list, ",")
var samples_info = `Sample beneficaries:`

func main() {
	
	if len(mbi_array) == len(hicn_array) && len(fhir_id_array) == len(hicn_array) && len(mbi_array) > 0 {
	  for i := 0; i < len(mbi_array); i++ {
		samples_info += fmt.Sprintf("{fhir_id=%s, mbi=%s, hicn=%s}", fhir_id_array[i], mbi_array[i], hicn_array[i])
	  }
	}

	t := template.Must(template.New("loginpage").Parse(login_template))
	http.Handle("/", logRequest(presentLogin(t)))

	http.Handle("/health", logRequest(http.HandlerFunc(handleHealth)))
	http.Handle("/login", logRequest(http.HandlerFunc(handleLogin)))
	http.Handle("/sso/session", logRequest(http.HandlerFunc(handleCode)))
	http.Handle("/v1/users/", logRequest(http.HandlerFunc(handleUserinfo)))
	http.ListenAndServe(":8080", nil)
}

func handleCode(rw http.ResponseWriter, r *http.Request) {
	body := &struct {
		Code string `json:"request_token"`
	}{}

	// Try to decode the request body into the struct. If there is an error,
	// respond to the client with the error message and a 400 status code.
	err := json.NewDecoder(r.Body).Decode(body)
	if err != nil {
		http.Error(rw, err.Error(), http.StatusBadRequest)
		return
	}

	tkn := code(body.Code)

	user_info := tkn.userinfo()

	token := map[string]string{
		"user_id": user_info.Sub,
		"auth_token": body.Code,
	}

	log.Println(token)
	rw.Header().Set("Content-Type", "application/json")
	json.NewEncoder(rw).Encode(token)
}

func handleHealth(rw http.ResponseWriter, r *http.Request) {
	all_is_well := map[string]string{
		"message": "all's well",
	}
	json.NewEncoder(rw).Encode(all_is_well)
}

func handleUserinfo(rw http.ResponseWriter, r *http.Request) {
	tkn := code(strings.Split(r.Header.Get(AUTH_HEADER), " ")[1])
	user_info := tkn.userinfo()
	slsx_userinfo := map[string]map[string]map[string]string{
		"data": {
			"user": {
				"id": user_info.Sub,
				"username": user_info.Name,
				"email": user_info.Email,
				"firstName": user_info.First_name,
				"lastName": user_info.Last_name,
				"hicn": user_info.Hicn,
				"mbi": user_info.Mbi,
			},
		},
	}
	json.NewEncoder(rw).Encode(slsx_userinfo)
}

func presentLogin(t *template.Template) http.Handler {
	return http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		var login_data LoginPageData
		login_data.HelpMessage = samples_info
		login_data.MbiValues = mbi_array
		login_data.HicnValues = hicn_array
		rw.Header().Set("Content-Type", "text/html; charset=utf-8")
		r.ParseForm()
		login_data.Relay = r.FormValue("relay")
		login_data.Redirect_uri = r.FormValue("redirect_uri")
		t.Execute(rw, login_data)
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
	q.Add("req_token", string(code))
	q.Add("relay", r.FormValue("relay"))

	u.RawQuery = q.Encode()

	http.Redirect(rw, r, u.String(), http.StatusFound)
}

func login(r *http.Request) code {
	usr := r.FormValue(USERNAME_FIELD)
	name := r.FormValue(NAME_FIELD)
	first_name := r.FormValue(FIRST_NAME_FIELD)
	last_name := r.FormValue(LAST_NAME_FIELD)
	email := r.FormValue(EMAIL_FIELD)
	hicn := r.FormValue(HICN_FIELD)
	mbi := r.FormValue(MBI_FIELD)

	return encode(usr, name, first_name, last_name, email, hicn, mbi)
}

type code string

func (c code) userinfo() *userinfo {
	usr, name, first_name, last_name, email, hicn, mbi := decode(string(c))
	return &userinfo{
		Sub:  usr,
		Name: name,
		First_name: first_name,
		Last_name: last_name,
		Email: email,
		Hicn: hicn,
		Mbi: mbi,
	}
}

func decode(c string) (string, string, string, string, string, string, string) {
	d_usr, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[0])
	d_name, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[1])
	d_first_name, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[2])
	d_last_name, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[3])
	d_email, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[4])
	d_hicn, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[5])
	d_mbi, _ := base64.RawURLEncoding.DecodeString(strings.Split(c, ".")[6])
	return string(d_usr), string(d_name), string(d_first_name), string(d_last_name),
	       string(d_email), string(d_hicn), string(d_mbi)
}

func encode(usr, name, first_name, last_name, email, hicn, mbi string) code {
	e_usr := base64.RawURLEncoding.EncodeToString([]byte(usr))
	e_name := base64.RawURLEncoding.EncodeToString([]byte(name))
	e_first_name := base64.RawURLEncoding.EncodeToString([]byte(first_name))
	e_last_name := base64.RawURLEncoding.EncodeToString([]byte(last_name))
	e_email := base64.RawURLEncoding.EncodeToString([]byte(email))
	e_hicn := base64.RawURLEncoding.EncodeToString([]byte(hicn))
	e_mbi := base64.RawURLEncoding.EncodeToString([]byte(mbi))
	return code(fmt.Sprintf("%s.%s.%s.%s.%s.%s.%s", e_usr, e_name, e_first_name,
				e_last_name, e_email, e_hicn, e_mbi))
}

type userinfo struct {
	Sub         	string `json:"sub"`
	Name        	string `json:"name"`
	First_name  	string `json:"first_name"`
	Last_name 	    string `json:"last_name"`
	Email       	string `json:"email"`
	Hicn   			string `json:"hicn"`
	Mbi   			string `json:"mbi"`
}

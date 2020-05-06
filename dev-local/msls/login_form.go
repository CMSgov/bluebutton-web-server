package main

var login_template = `
<form method="post" action="/login">
<input type="text" name="username"></input>
<input type="text" name="password"></input>

<input type="hidden" name="state" value="{{ .Get "state" }}"></input>
<input type="hidden" name="redirect_uri" value="{{ .Get "redirect_uri" }}"></input>
<button type="submit">Sign In</button>
</form>
`

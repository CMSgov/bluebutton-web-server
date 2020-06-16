package main

var login_template = `
<style>
label{
    display: inline-block;
    float: left;
    clear: left;
    width: 250px;
    text-align: left; /*Change to right here if you want it close to the inputs*/
}
input {
  display: inline-block;
  float: left;
}
.container {
  width: 500px;
  clear: both;
}
.container input {
  width: 100%;
  clear: both;
}
.txtwrapleft {
  float: left;
  margin: 10px;
}
submit{
  padding-left: 100px;
}
</style>

<h1>MSLS Component Inputs for simulating SLS/MyMedicare auth flow locally</h1>
<p>
<img class="txtwrapleft" alt="BB2 Local Dev Warning" src="data:image/png;base64,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">
<h2>Simulated Authentication no PHI or PII</h2>
<h2>Use Only Synthetic Beneficiary Info</h2>
<h2>Enter values to be returned by the SLS user_info endpoint below:</h2>
</p>
<br>
<br>
<form method="post" action="/login">
<div>
    <h3>Enter User Name:</h3>
    <label>SUB(username): </label> <input type="text" name="username" size=50></input>
    <br>
    <h3>Enter Identity:</h3>
    <label>BENE Id, HICN or HICN HASH, MBI or MBI HASH Accepted</label> <input type="text" name="usr_identity" size=64></input>
    <br>
    <br>
    <p><b>Select Identity Type:</b></p>
    <input type="radio" id="is_hicn" name="beneficiary_identity" value="H" checked="checked">HICN</input>
    <br>
    <input type="radio" id="is_hicn_hash" name="beneficiary_identity" value="HH" disabled>HICN Hash</input>
    <br>
    <input type="radio" id="is_mbi" name="beneficiary_identity" value="M">MBI</input>
    <br>
    <input type="radio" id="is_mbi_hash" name="beneficiary_identity" value="MH" disabled>MBI Hash</input>
    <br>
    <input type="radio" id="is_bene_id" name="beneficiary_identity" value="S" disabled>BENE ID</input>
    <br>
    <br>
    <label>name</label> <input type="text" name="name" size=30></input>
    <br>
    <br>
    <label>given_name</label> <input type="text" name="given_name" size=50></input>
    <br>
    <br>
    <label>family_name</label> <input type="text" name="family_name" size=50></input>
    <br>
    <br>
    <label>email</label> <input type="text" name="email" size=80></input>
    <br>
    <br>
    <input type="hidden" name="state" value="{{ .Get "state" }}"></input>
    <input type="hidden" name="redirect_uri" value="{{ .Get "redirect_uri" }}"></input>
    <button type="submit">Sign In</button>
</div>
</form>
`

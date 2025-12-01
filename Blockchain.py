from flask import Flask, render_template_string, request, redirect, session, url_for
import hashlib
import json
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

# ---------------- Setup Flask ----------------
app = Flask(__name__)
app.secret_key = "replace_this_with_a_random_secret!"  # change for production

# ---------------- Blockchain core ----------------
class Block:
    def __init__(self, index, data, timestamp, previous_hash):
        self.index = index
        self.data = data
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_dict = {
            "index": self.index,
            "data": self.data,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash
        }
        block_string = json.dumps(block_dict, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_data = {"message": "GENESIS BLOCK"}
        genesis = Block(0, genesis_data, datetime.utcnow().isoformat(), "0")
        self.chain.append(genesis)

    def add_block(self, data):
        prev = self.chain[-1]
        new_block = Block(len(self.chain), data, datetime.utcnow().isoformat(), prev.hash)
        self.chain.append(new_block)
        return new_block

    def to_list(self):
        out = []
        for b in self.chain:
            out.append({
                "index": b.index,
                "timestamp": b.timestamp,
                "data": b.data,
                "previous_hash": b.previous_hash,
                "hash": b.hash
            })
        return out

blockchain = Blockchain()

# ---------------- Digital signatures ----------------
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

def sign_data_string(s: str) -> bytes:
    return private_key.sign(
        s.encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )

def verify_signature_string(s: str, signature_bytes: bytes) -> bool:
    try:
        public_key.verify(
            signature_bytes,
            s.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

# ---------------- Navigation ----------------
NAV = """
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <a class="navbar-brand" href="/">ParkingChain</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarsExample">
      <span class="navbar-toggler-icon"></span>
    </button>

    <div class="collapse navbar-collapse" id="navbarsExample">
      <ul class="navbar-nav ms-auto mb-2 mb-lg-0">
        <li class="nav-item"><a class="nav-link" href="/">Reserve</a></li>
        <li class="nav-item"><a class="nav-link" href="/ledger-login">Ledger</a></li>
        <li class="nav-item"><a class="nav-link" href="/about">About</a></li>
        <li class="nav-item"><a class="nav-link" href="/contact">Contact</a></li>
      </ul>
    </div>
  </div>
</nav>
"""

# ---------------- GLOBAL CSS ----------------
GLOBAL_CSS = """<style>
body {
    background: url('https://images.unsplash.com/photo-1746130173495-3f26e86a484e?q=80&w=1170&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')
                no-repeat center center fixed;
    background-size: cover;
    font-family: "Segoe UI", Roboto, sans-serif;
    margin:0;
    padding:0;
}
.page-overlay {
    background: rgba(255,255,255,0.72);
    backdrop-filter: blur(6px);
    min-height: 100vh;
    padding-bottom: 50px;
}

/* Navbar */
nav.navbar {
    backdrop-filter: blur(12px);
    background: rgba(0,0,0,0.65) !important;
    box-shadow: 0 4px 18px rgba(0,0,0,0.45);
}
nav a.nav-link { font-weight:500; }

/* Hero */
.hero-section {
    position: relative;
    height: 360px;
    background-image: url('https://www.reliance-foundry.com/wp-content/uploads/how-airport-parking-works.jpg.webp');
    background-size: 360px;
    background-position: 360px;
}
.hero-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to bottom, rgba(0,0,0,0.25), rgba(0,0,0,0.65));
}
.hero-text {
    position: absolute;
    bottom: 28px;
    left: 50%;
    transform: translateX(-50%);
    color: white;
    text-shadow: 0 4px 12px rgba(0,0,0,0.45);
    text-align: center;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.82);
    backdrop-filter: blur(10px);
    border-radius:14px;
    border:none;
    box-shadow:0 10px 26px rgba(0,0,0,0.25);
}

/* Inputs */
input, select, textarea {
    border-radius:10px !important;
    border:1px solid #c2c8d5 !important;
    padding:10px !important;
    background: rgba(255,255,255,0.9) !important;
}
input:focus, select:focus, textarea:focus {
    border-color:#0066ff !important;
    box-shadow:0 0 0 4px rgba(0,102,255,0.25) !important;
}

/* Buttons */
.btn-primary {
    background: linear-gradient(135deg, #0066ff, #004bcc);
    border:none;
    border-radius:10px;
    font-weight:600;
    padding:10px 20px;
    transition:0.2s;
}
.btn-primary:hover {
    background: linear-gradient(135deg, #0055dd, #003cb0);
}

/* Ledger Card */
.ledger-card {
    background: rgba(15,23,42,0.88);
    backdrop-filter: blur(10px);
    color: #e2e8f0;
    border-radius:12px;
    padding:18px;
    box-shadow:0 4px 18px rgba(0,0,0,0.25);
}

/* Verified and Invalid */
.status-verified {
    color: #4ade80; /* green */
    font-weight: 700;
}
.status-invalid {
    color: #f87171; /* red */
    font-weight: 700;
}
</style>"""

# ---------------- HTML Templates ----------------
HOME_HTML = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Airport Parking Reservation</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  {GLOBAL_CSS}
</head>
<body>
<div class="page-overlay">

<!-- HERO BANNER -->
<div class="hero-section">
  <div class="hero-overlay"></div>
  <div class="hero-text">
      <h1 style="font-weight:700; font-size:2.8rem;">Airport Parking Reservation</h1>
      <p style="font-size:1.25rem; opacity:0.9;">Secure • Verified • Blockchain-backed</p>
  </div>
</div>

{NAV}

<div class="container mt-4">
  <div class="card shadow-sm">
    <div class="card-body">

      <form method="POST">
        <h3 class="card-title">Reserve Your Parking</h3>

        <div class="row">
          <div class="col-md-6 mb-3"><label>First Name</label><input name="first" class="form-control" required></div>
          <div class="col-md-6 mb-3"><label>Last Name</label><input name="last" class="form-control" required></div>
        </div>

        <div class="row">
          <div class="col-md-6 mb-3"><label>License Plate</label><input name="plate" class="form-control" required></div>
          <div class="col-md-6 mb-3">
            <label>Parking Spot</label>
            <select name="spot" class="form-select" required>
              <option value="A1">A1</option>
              <option value="A2">A2</option>
              <option value="B1">B1</option>
              <option value="B2">B2</option>
            </select>
          </div>
        </div>

        <div class="row">
          <div class="col-md-6 mb-3"><label>Car Make</label><input name="make" class="form-control" required></div>
          <div class="col-md-6 mb-3"><label>Car Model</label><input name="model" class="form-control" required></div>
        </div>

        <div class="row">
          <div class="col-md-6 mb-3"><label>Pickup</label><input name="pickup" type="datetime-local" class="form-control" required></div>
          <div class="col-md-6 mb-3"><label>Dropoff</label><input name="dropoff" type="datetime-local" class="form-control" required></div>
        </div>

        <button class="btn btn-primary w-100">Reserve Parking</button>
      </form>

    </div>
  </div>

  <div class="text-center mt-3">
    <a href="/ledger-login" class="btn btn-outline-secondary">View Ledger (PIN required)</a>
  </div>
</div>
</div>
</body>
</html>
"""

CONFIRM_HTML = f"""
<!doctype html>
<html>
<head>
  <title>Reservation Confirmed</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  {GLOBAL_CSS}
</head>
<body>
<div class="page-overlay">
{NAV}
<div class="container mt-5">
  <div class="card text-center">
    <div class="card-body">
      <h2>🎉 Reservation Confirmed!</h2>
      <p>Your reservation is secured and stored on the blockchain.</p>
      <a href="/" class="btn btn-primary">Make Another</a>
      <a href="/ledger-login" class="btn btn-outline-secondary">View Ledger</a>
    </div>
  </div>
</div>
</div>
</body>
</html>
"""

LEDGER_LOGIN_HTML = f"""
<!doctype html>
<html>
<head>
  <title>Ledger Login</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  {GLOBAL_CSS}
</head>
<body>
<div class="page-overlay">
{NAV}
<div class="container mt-5" style="max-width:420px;">
  <div class="card">
    <div class="card-body">

      <h4>Enter PIN</h4>

      {{% if error %}}
        <div class="alert alert-danger">{{{{ error }}}}</div>
      {{% endif %}}

      <form method="POST">
        <input name="pin" type="password" class="form-control mb-3" required>
        <button class="btn btn-primary w-100">Enter</button>
      </form>

    </div>
  </div>
</div>
</div>
</body>
</html>
"""

LEDGER_HTML = f"""
<!doctype html>
<html>
<head>
  <title>Blockchain Ledger</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  {GLOBAL_CSS}
</head>
<body>
<div class="page-overlay">
{NAV}
<div class="container mt-4">
  <h3>Blockchain Ledger</h3>
  <a href="/" class="btn btn-secondary mb-3">← Back</a>

  {{% for b in chain %}}
    {{% if b.data.signature is defined %}}
    <div class="ledger-card mb-3" style="{{% if not b.signature_valid %}}border: 2px solid #f87171;{{% else %}}border: 2px solid #4ade80;{{% endif %}}">
      <h5>Block #{{{{ b.index }}}} - <small>{{{{ b.timestamp }}}}</small></h5>
      <p><strong>Name:</strong> {{{{ b.data.first }}}} {{{{ b.data.last }}}}</p>
      <p><strong>Plate:</strong> {{{{ b.data.plate }}}}</p>
      <p><strong>Car:</strong> {{{{ b.data.make }}}} {{{{ b.data.model }}}}</p>
      <p><strong>Spot:</strong> {{{{ b.data.spot }}}}</p>
      <p><strong>Signature:</strong> {{{{ b.data.signature[:80] }}}}...</p>
      <p>Status: 
        {{% if b.signature_valid %}}
          <span class="status-verified">✔ Verified</span>
        {{% else %}}
          <span class="status-invalid">✘ Invalid Signature</span>
        {{% endif %}}
      </p>
    </div>
    {{% endif %}}
  {{% endfor %}}
</div>
</div>
</body>
</html>
"""

ABOUT_HTML = f"""
<!doctype html>
<html><head>
<title>About</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
{GLOBAL_CSS}
</head>
<body>
<div class="page-overlay">
{NAV}
<div class="container mt-5">
  <h2>About This Project</h2>
  <p>A blockchain-backed airport parking system using SHA-256 and RSA signatures.</p>
</div>
</div>
</body></html>
"""

CONTACT_HTML = f"""
<!doctype html>
<html><head>
<title>Contact</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
{GLOBAL_CSS}
</head><body>
<div class="page-overlay">
{NAV}
<div class="container mt-5">
  <h2>Contact Us</h2>
  <form method="POST">
    <input name="name" class="form-control mb-3" placeholder="Your name" required>
    <input name="email" class="form-control mb-3" type="email" placeholder="Email" required>
    <textarea name="message" class="form-control mb-3" rows="4" required></textarea>
    <button class="btn btn-primary">Send</button>
  </form>
</div>
</div>
</body></html>
"""

CONTACT_SUCCESS_HTML = f"""
<!doctype html>
<html><head>
<title>Message Sent</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
{GLOBAL_CSS}
</head><body>
<div class="page-overlay">
{NAV}
<div class="container mt-5 text-center">
  <div class="card"><div class="card-body">
    <h4>Message Sent</h4>
    <p>We will get back to you soon.</p>
    <a href="/" class="btn btn-primary">Home</a>
  </div></div>
</div>
</div>
</body></html>
"""

# ---------------- Routes ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        first = request.form.get("first")
        last = request.form.get("last")
        plate = request.form.get("plate")
        make = request.form.get("make")
        model = request.form.get("model")
        spot = request.form.get("spot")
        pickup = request.form.get("pickup")
        dropoff = request.form.get("dropoff")

        data = {
            "first": first, "last": last, "plate": plate,
            "make": make, "model": model,
            "spot": spot, "pickup": pickup, "dropoff": dropoff
        }

        sign_text = f"{first}|{last}|{plate}|{make}|{model}|{spot}|{pickup}|{dropoff}"
        signature = sign_data_string(sign_text)
        data["signature"] = signature.hex()

        blockchain.add_block(data)
        return render_template_string(CONFIRM_HTML)

    return render_template_string(HOME_HTML)

@app.route("/ledger-login", methods=["GET", "POST"])
def ledger_login():
    error = None
    if request.method == "POST":
        if request.form.get("pin") == "2221":
            session["authenticated"] = True
            return redirect(url_for("ledger"))
        error = "Incorrect PIN"
    return render_template_string(LEDGER_LOGIN_HTML, error=error)

@app.route("/ledger")
def ledger():
    if not session.get("authenticated"):
        return redirect(url_for("ledger_login"))

    chain = blockchain.to_list()

    # Verify signatures for each block that has a signature
    for block in chain:
        data = block["data"]
        if "signature" in data:
            sign_text = f"{data.get('first','')}|{data.get('last','')}|{data.get('plate','')}|{data.get('make','')}|{data.get('model','')}|{data.get('spot','')}|{data.get('pickup','')}|{data.get('dropoff','')}"
            signature_bytes = bytes.fromhex(data["signature"])
            block["signature_valid"] = verify_signature_string(sign_text, signature_bytes)
        else:
            block["signature_valid"] = None

    return render_template_string(LEDGER_HTML, chain=chain)

@app.route("/about")
def about():
    return render_template_string(ABOUT_HTML)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        print("Contact:", request.form.get("name"), request.form.get("email"), request.form.get("message"))
        return render_template_string(CONTACT_SUCCESS_HTML)
    return render_template_string(CONTACT_HTML)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

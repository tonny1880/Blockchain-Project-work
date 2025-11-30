from flask import Flask, request, jsonify, render_template_string
import hashlib
import json
import time
import os

app = Flask(__name__)

# =====================================================
#                    BLOCKCHAIN CLASS
# =====================================================
class Blockchain:
    def __init__(self, file="parking_chain.json"):
        self.file = file
        self.chain = []
        self.load_chain()

    def create_genesis_block(self):
        block = {
            "index": 0,
            "timestamp": time.time(),
            "data": "GENESIS BLOCK",
            "prev_hash": "0",
        }
        block["hash"] = self.hash_block(block)
        self.chain.append(block)
        self.save_chain()

    def load_chain(self):
        if os.path.exists(self.file):
            with open(self.file, "r") as f:
                self.chain = json.load(f)
        else:
            self.create_genesis_block()

    def save_chain(self):
        with open(self.file, "w") as f:
            json.dump(self.chain, f, indent=4)

    def hash_block(self, block):
        block_copy = block.copy()
        block_copy.pop("hash", None)
        encoded = json.dumps(block_copy, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    def add_block(self, data):
        last = self.chain[-1]
        block = {
            "index": len(self.chain),
            "timestamp": time.time(),
            "data": data,
            "prev_hash": last["hash"]
        }
        block["hash"] = self.hash_block(block)
        self.chain.append(block)
        self.save_chain()
        return block

    def validate_chain(self):
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr["prev_hash"] != prev["hash"]:
                return False
            if curr["hash"] != self.hash_block(curr):
                return False
        return True


blockchain = Blockchain()

# =====================================================
#                 RESERVATION SYSTEM
# =====================================================
reservations = []  # in-memory for easy checking

def slot_is_available(slot, start, end):
    for r in reservations:
        if r["slot"] == slot:
            # time overlap check
            if not (end <= r["start"] or start >= r["end"]):
                return False
    return True

HTML = """
<h1>Airport Parking Reservation (Blockchain Powered)</h1>

<h2>Make a Reservation</h2>
<form method="POST" action="/reserve">
  User Name: <input name="user"><br><br>
  Slot Number: <input name="slot" type="number"><br><br>
  Start Time (unix timestamp): <input name="start" type="number"><br><br>
  End Time (unix timestamp): <input name="end" type="number"><br><br>
  <button type="submit">Reserve</button>
</form>

<h2>Blockchain</h2>
<pre>{{ chain }}</pre>
"""

# =====================================================
#                    ROUTES
# =====================================================
@app.route("/")
def home():
    return render_template_string(HTML, chain=json.dumps(blockchain.chain, indent=4))

@app.route("/reserve", methods=["POST"])
def reserve():
    user = request.form.get("user")
    slot = int(request.form.get("slot"))
    start = int(request.form.get("start"))
    end = int(request.form.get("end"))

    if start >= end:
        return jsonify({"error": "End time must be greater than start time"}), 400

    if not slot_is_available(slot, start, end):
        return jsonify({"error": "Slot is already booked for that time"}), 400

    # Create reservation record
    reservation_id = hashlib.sha256(f"{user}{slot}{start}{end}{time.time()}".encode()).hexdigest()

    reservation = {
        "reservation_id": reservation_id,
        "user": user,
        "slot": slot,
        "start": start,
        "end": end,
    }

    reservations.append(reservation)

    # Store on blockchain
    block = blockchain.add_block(reservation)

    return jsonify({
        "message": "Reservation successful!",
        "reservation": reservation,
        "block": block
    })

@app.route("/chain")
def chain():
    return jsonify({
        "valid_chain": blockchain.validate_chain(),
        "chain": blockchain.chain
    })

# =====================================================
#                    MAIN
# =====================================================
if __name__ == "__main__":
    app.run(port=5000, debug=True)


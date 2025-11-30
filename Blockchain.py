import json
import hashlib
import time
import tkinter as tk
from tkinter import messagebox, ttk
from ecdsa import SigningKey, VerifyingKey, NIST256p

class Wallet:
    def __init__(self):
        self.private = SigningKey.generate(curve=NIST256p)
        self.public = self.private.get_verifying_key()

    def sign(self, data):
        return self.private.sign(data.encode()).hex()

    def get_address(self):
        return self.public.to_string().hex()

class Block:
    def __init__(self, index, transactions, prev_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.prev_hash = prev_hash
        self.timestamp = time.time()
        self.nonce = nonce

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending = []
        self.difficulty = 3
        self.create_genesis()

    def create_genesis(self):
        g = Block(0, [], "0")
        g.hash = g.compute_hash()
        self.chain.append(g)

    def add_transaction(self, sender, receiver, amount, signature, pubkey_hex):
        try:
            pub = VerifyingKey.from_string(bytes.fromhex(pubkey_hex), curve=NIST256p)
            pub.verify(bytes.fromhex(signature), f"{sender}{receiver}{amount}".encode())
            self.pending.append({
                "sender": sender,
                "receiver": receiver,
                "amount": amount,
                "signature": signature,
                "pubkey": pubkey_hex
            })
            return True
        except:
            return False

    def mine(self):
        if not self.pending:
            return None
        last = self.chain[-1]
        block = Block(len(self.chain), self.pending, last.compute_hash())
        block.hash = self.proof_of_work(block)
        self.chain.append(block)
        self.pending = []
        return block.hash

    def proof_of_work(self, block):
        block.nonce = 0
        h = block.compute_hash()
        while not h.startswith("0" * self.difficulty):
            block.nonce += 1
            h = block.compute_hash()
        return h

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Blockchain Demo")

        self.bc = Blockchain()
        self.wallet = Wallet()

        self.addr_lbl = tk.Label(root, text="Your Address:")
        self.addr_lbl.pack()
        self.addr_box = tk.Entry(root, width=80)
        self.addr_box.insert(0, self.wallet.get_address())
        self.addr_box.pack()

        tk.Label(root, text="Send To:").pack()
        self.send_to = tk.Entry(root, width=50)
        self.send_to.pack()

        tk.Label(root, text="Amount:").pack()
        self.amount = tk.Entry(root, width=20)
        self.amount.pack()

        self.btn_tx = tk.Button(root, text="Create Transaction", command=self.create_tx)
        self.btn_tx.pack(pady=5)

        self.btn_mine = tk.Button(root, text="Mine Block", command=self.mine_block)
        self.btn_mine.pack(pady=5)

        tk.Label(root, text="Blockchain Explorer").pack()
        self.tree = ttk.Treeview(root, columns=("index", "hash"), show="headings")
        self.tree.heading("index", text="Index")
        self.tree.heading("hash", text="Hash")
        self.tree.pack(fill="both", expand=True)

        self.refresh()

    def create_tx(self):
        receiver = self.send_to.get()
        amount = self.amount.get()

        if not receiver or not amount.isdigit():
            messagebox.showerror("Error", "Invalid Transaction")
            return

        payload = f"{self.wallet.get_address()}{receiver}{amount}"
        signature = self.wallet.sign(payload)

        if self.bc.add_transaction(
            self.wallet.get_address(), receiver, amount, signature, self.wallet.get_address()
        ):
            messagebox.showinfo("Success", "Transaction Added")
        else:
            messagebox.showerror("Error", "Signature Failed")

    def mine_block(self):
        h = self.bc.mine()
        if h:
            messagebox.showinfo("Mined", f"Block Mined:\n{h}")
            self.refresh()
        else:
            messagebox.showinfo("Info", "No pending transactions")

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for b in self.bc.chain:
            self.tree.insert("", "end", values=(b.index, b.compute_hash()))

root = tk.Tk()
app = App(root)
root.mainloop()

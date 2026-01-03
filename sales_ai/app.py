from flask import Flask, render_template, request, redirect, session
import pandas as pd
import os

# 🔴 IMPORTANT FIX (matplotlib thread error)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "secret123"

ADMIN = ("admin", "admin123")
VIEWER = ("viewer", "view123")

BASE = "data/users"

def user_folder(user):
    path = os.path.join(BASE, user)
    os.makedirs(path, exist_ok=True)
    return path

def excel(user, file):
    return os.path.join(user_folder(user), file)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form["username"]
        session["pass"] = request.form["password"]
        return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    u = session["user"]
    p = session["pass"]

    role = "public"
    if (u, p) == ADMIN:
        role = "admin"
    elif (u, p) == VIEWER:
        role = "viewer"

    sale_f = excel(u, "sale.xlsx")
    exp_f = excel(u, "expense.xlsx")

    if request.method == "POST" and role != "viewer":
        t = request.form.get("type")

        if t == "sale":
            amount = float(request.form.get("amount", 0))
            discount = float(request.form.get("discount", 0))
            net = amount - discount

            df = pd.DataFrame([{
                "Item": request.form.get("item", ""),
                "Amount": amount,
                "Discount": discount,
                "Net Sale": net
            }])

            old = pd.read_excel(sale_f) if os.path.exists(sale_f) else pd.DataFrame()
            pd.concat([old, df], ignore_index=True).to_excel(sale_f, index=False)

        if t == "expense":
            df = pd.DataFrame([{
                "Item": request.form.get("item", ""),
                "Expense": float(request.form.get("amount", 0))
            }])

            old = pd.read_excel(exp_f) if os.path.exists(exp_f) else pd.DataFrame()
            pd.concat([old, df], ignore_index=True).to_excel(exp_f, index=False)

    sale = pd.read_excel(sale_f) if os.path.exists(sale_f) else pd.DataFrame()
    exp = pd.read_excel(exp_f) if os.path.exists(exp_f) else pd.DataFrame()

    total_sale = sale["Net Sale"].sum() if not sale.empty else 0
    total_exp = exp["Expense"].sum() if not exp.empty else 0
    banking = total_sale - total_exp

    # ✅ SAFE GRAPH CODE
    plt.clf()
    plt.bar(["Sale", "Expense", "Banking"], [total_sale, total_exp, banking])
    os.makedirs("static", exist_ok=True)
    plt.savefig("static/graph.png")
    plt.close()

    return render_template(
        "dashboard.html",
        role=role,
        sale=sale.to_html(index=False),
        expense=exp.to_html(index=False),
        sale_total=total_sale,
        exp_total=total_exp,
        bank=banking
    )

@app.route("/delete")
def delete():
    u = session.get("user")
    if u:
        for f in os.listdir(user_folder(u)):
            os.remove(os.path.join(user_folder(u), f))
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
      app.run()
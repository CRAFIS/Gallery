# -*- coding: utf-8 -*-

from flask import Flask, render_template, redirect
from flask import request, url_for, jsonify, session
import os, re, db, datetime, random, auth

app = Flask(__name__)

app.secret_key = "FY2TCPEUY8UZWYHLWXNR"

@app.route("/")
def index():
    db.create()
    if db.getAllUser() == []:
        session["username"] = "Anonymous"
        session["type"] = "curator"
    story = db.getAllStory()
    story = [scene for scene in story if scene["parent_id"] == None]
    story = sorted(story, key = lambda scene: scene["id"])
    if session.get("type") == "curator":
        session["x_ratio"], session["y_ratio"] = None, None
        return render_template("curator.html", session = session, story = story)
    return render_template("index.html", session = session, story = story)

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        user = db.getUser(request.form["username"])
        if auth.auth(user, request.form["password"]):
            if not session:
                session["username"] = user["name"]
                session["type"] = user["type"]
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/sign_up", methods = ["GET", "POST"])
def sign_up():
    if session.get("type") == "visitor":
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form["username"]
        user = db.getUser(username)
        if not user:
            salt = ''.join([random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(20)])
            password = auth.getHash(request.form["password"] + salt)
            if session.get("type") == "curator":
                db.addUser(username, "curator", password, salt)
            else:
                db.addUser(username, "visitor", password, salt)
                session["username"] = username
                session["type"] = "visitor"
            return redirect(url_for("index"))
    return render_template("sign_up.html")

@app.route("/scene", methods = ["GET"])
def scene():
    if request.method == "GET":
        scene_id = request.args.get("id", type = int)
        story = db.getAllStory()
        scene = [scene for scene in story if scene_id == scene["id"]]
        allFeedback = reversed(db.selectFeedback(scene_id))
        if scene != []:
            child = [scene for scene in story if scene_id == scene["parent_id"]]
            return render_template("scene.html", session = session, scene = scene[0], child = child, allFeedback = allFeedback)
    return redirect(url_for("index"))

@app.route("/add_scene", methods = ["GET", "POST"])
def add_scene():
    if session.get("type") == "curator" and request.method == "POST":
        scene_id = int(request.form["id"])
        scene = db.get_scene(scene_id)
        if not scene: scene = {"id": 0, "type": None}
        session["x_ratio"] = request.form.get("x_ratio", session["x_ratio"])
        session["y_ratio"] = request.form.get("y_ratio", session["y_ratio"])
        return render_template("add_scene.html", session = session, scene = scene)
    return redirect(url_for("index"))

@app.route("/execute_add_scene", methods = ["GET", "POST"])
def execute_add_scene():
    if session.get("type") == "curator" and request.method == "POST":
        img_file = request.files["img_file"]
        parent_id = int(request.form["id"])
        title = request.form["title"]
        scene_type = request.form["type"]
        if parent_id == 0: parent_id = None
        scene = db.add_scene(title, "", scene_type, parent_id)
        path = "data/{}.jpg".format(scene['id'])
        img_file.save("./static/" + path)
        db.update_scene(scene["id"], "path", path)
        if session.get("x_ratio") and session.get("y_ratio"):
            db.add_to_panorama(parent_id, None, float(session["x_ratio"]), float(session["y_ratio"]))
    return redirect(url_for("index"))

@app.route("/delete_scene", methods = ["GET", "POST"])
def delete_scene():
    if session.get("type") == "curator" and request.method == "POST":
        db.delete_scene(request.form["id"])
    return redirect(url_for("index"))

@app.route("/add_feedback", methods = ["GET", "POST"])
def add_feedback():
    if session.get("type") == "visitor" and request.method == "POST":
        user = db.getUserID(session.get("username"))
        user_id = int(user['id'])
        message = request.form["message"]
        date = datetime.datetime.today().strftime("%Y/%m/%d %H:%M:%S")
        scene_id = int(request.form["id"])
        db.addFeedback(int(user_id), str(message), str(date), int(scene_id))
    return redirect(url_for("index"))

@app.route("/delete_feedback", methods = ["GET", "POST"])
def delete_feedback():
    if session.get("type") == "curator" and request.method == "POST":
        db.deleteFeedback(request.form["feedback_id"])
    return redirect(url_for("index"))

@app.route("/upload", methods = ["GET", "POST"])
def upload():
    if session.get("type") == "curator":
        return render_template("upload.html")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = 8888
    app.debug = True
    app.run(host = "localhost", port = port)

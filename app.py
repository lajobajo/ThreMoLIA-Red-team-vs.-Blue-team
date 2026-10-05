from flask import Flask, render_template, redirect, url_for, session, request

app = Flask(__name__)

app.secret_key = "dev-secret-key"


@app.route("/")
def home():
    if not session.get("game_started"):
        return render_template("start.html")

    if session.get("phase") == "handover":
        return render_template(
            "handover.html",
            next_team=session["next_team"],
            round_number=session["round"]
        )

    return render_template(
        "turn.html",
        team=session["current_team"],
        round_number=session["round"],
        blue_action=session.get("blue_action")
    )


@app.route("/start", methods=["POST"])
def start():
    session["game_started"] = True
    session["current_team"] = "blue"
    session["round"] = 1
    session["phase"] = "turn"

    # Blue Team state
    session["blue_action"] = None
    session["blue_locked"] = False

    # Red Team state
    session["red_action"] = None
    session["red_locked"] = False

    return redirect(url_for("home"))

@app.route("/dfd")
def dfd():
    if not session.get("game_started"):
        return redirect(url_for("home"))

    return render_template(
        "dfd.html",
        team=session["current_team"],
        round_number=session["round"]
    )

@app.route("/blue-action", methods=["POST"])
def blue_action():
    if not session.get("game_started"):
        return redirect(url_for("home"))

    if session.get("current_team") != "blue":
        return redirect(url_for("home"))

    vulnerability = request.form.get("vulnerability")

    if not vulnerability:
        return redirect(url_for("home"))

    session["blue_action"] = vulnerability
    session["blue_locked"] = True

    return redirect(url_for("home"))

@app.route("/end-turn", methods=["POST"])
def end_turn():
    if not session.get("game_started"):
        return redirect(url_for("home"))

    current_team = session["current_team"]

    if current_team == "blue":

        # Blue must make a choice before ending the turn
        if not session.get("blue_locked"):
            return redirect(url_for("home"))

        session["next_team"] = "red"
        session["phase"] = "handover"

    else:

        # Red logic will be added later
        session["round"] += 1
        session["next_team"] = "blue"
        session["phase"] = "handover"

    return redirect(url_for("home"))

@app.route("/continue", methods=["POST"])
def continue_game():
    if not session.get("game_started"):
        return redirect(url_for("home"))

    session["current_team"] = session["next_team"]
    session["phase"] = "turn"

    return redirect(url_for("home"))


@app.route("/reset")
def reset():
    session.clear()

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)

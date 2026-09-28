from flask import Flask, render_template, redirect, url_for, session

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
        round_number=session["round"]
    )


@app.route("/start", methods=["POST"])
def start():
    session["game_started"] = True
    session["current_team"] = "blue"
    session["round"] = 1
    session["phase"] = "turn"

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


@app.route("/end-turn", methods=["POST"])
def end_turn():
    if not session.get("game_started"):
        return redirect(url_for("home"))

    current_team = session["current_team"]

    if current_team == "blue":
        session["next_team"] = "red"
        session["phase"] = "handover"

    else:
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

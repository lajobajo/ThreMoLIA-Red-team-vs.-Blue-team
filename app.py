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
        blue_action=session.get("blue_action"),
        blue_mitigation=session.get("blue_mitigation"),
        blue_budget=session.get("blue_budget"),
        blue_threats=session.get("blue_threats", []),
        blue_threat_model_locked=session.get(
            "blue_threat_model_locked",
            False
        ),
        red_action=session.get("red_action"),
        red_target=session.get("red_target")
    )


@app.route("/start", methods=["POST"])
def start():
    session["game_started"] = True
    session["current_team"] = "blue"
    session["round"] = 1
    session["phase"] = "turn"

# Blue Team state
    session["blue_action"] = None
    session["blue_mitigation"] = None
    session["blue_budget"] = 10
    session["blue_locked"] = False
    session["blue_threats"] = []
    session["blue_threat_model_locked"] = False
# Red Team state
    session["red_action"] = None
    session["red_target"] = None
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

@app.route("/blue-threat-model", methods=["POST"])
def blue_threat_model():
    if not session.get("game_started"):
        return redirect(url_for("home"))

    if session.get("current_team") != "blue":
        return redirect(url_for("home"))

    action = request.form.get("action")

    threat = request.form.get("threat", "").strip()
    target = request.form.get("target", "").strip()
    stride = request.form.get("stride", "").strip()

    threats = session.get("blue_threats", [])

    # Add threat
    if action == "add":

        if threat and target and stride:
            threats.append({
                "threat": threat,
                "target": target,
                "stride": stride
            })

        session["blue_threats"] = threats

        return redirect(url_for("home"))

    # Lock threat model
    if action == "lock":

        if threat and target and stride:
            threats.append({
                "threat": threat,
                "target": target,
                "stride": stride
            })

        if not threats:
            return redirect(url_for("home"))

        session["blue_threats"] = threats
        session["blue_threat_model_locked"] = True

        return redirect(url_for("home"))

    return redirect(url_for("home"))

@app.route("/red-action", methods=["POST"])
def red_action():
    if not session.get("game_started"):
        return redirect(url_for("home"))

    if session.get("current_team") != "red":
        return redirect(url_for("home"))

    attack = request.form.get("attack")
    target = request.form.get("target")

    if not attack or not target:
        return redirect(url_for("home"))

    session["red_action"] = attack
    session["red_target"] = target
    session["red_locked"] = True

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
        # Red must make a choice before ending the turn
        if not session.get("red_locked"):
            return redirect(url_for("home"))

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

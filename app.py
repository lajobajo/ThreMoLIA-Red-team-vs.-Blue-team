from flask import (
    Flask, render_template, redirect, url_for, session, request, flash
)

import game_data

app = Flask(__name__)

app.secret_key = "dev-secret-key"

@app.route("/")
def home():
    if not session.get("game_started"):
        return render_template("start.html")

    # Session from an older version of the game: start over
    if "blue_mitigations" not in session or "red_attacks" not in session:
        session.clear()
        return render_template("start.html")

    if session.get("phase") == "handover":
        return render_template(
            "handover.html",
            next_team=session["next_team"],
            round_number=session["round"]
        )

    if session.get("phase") == "result":
        return render_template(
            "result.html",
            round_number=session["round"],
            result=game_data.resolve(
                session["red_attacks"],
                session["blue_mitigations"]
            ),
            budget=session["blue_budget"]
        )

    if (
        session["current_team"] == "blue"
        and session.get("blue_step") == "mitigation"
    ):
        return render_template(
            "mitigation.html",
            round_number=session["round"],
            blue_threats=session.get("blue_threats", []),
            blue_budget=session["blue_budget"],
            blue_mitigations=session["blue_mitigations"],
            blue_mitigations_locked=session["blue_mitigations_locked"],
            mitigations=game_data.MITIGATIONS,
            nodes=game_data.NODES,
            attacks=game_data.ATTACKS
        )

    return render_template(
        "turn.html",
        team=session["current_team"],
        round_number=session["round"],
        blue_threats=session.get("blue_threats", []),
        blue_threat_model_locked=session.get(
            "blue_threat_model_locked",
            False
        ),
        red_attacks=session.get("red_attacks", []),
        red_locked=session.get("red_locked", False),
        attacks=game_data.ATTACKS,
        nodes=game_data.NODES,
        attacks_per_game=game_data.ATTACKS_PER_GAME
    )


@app.route("/start", methods=["POST"])
def start():
    session["game_started"] = True
    session["current_team"] = "blue"
    session["round"] = 1
    session["phase"] = "turn"
    session["blue_step"] = "threat_model"

# Blue Team state
    session["blue_budget"] = 10
    session["blue_threats"] = []
    session["blue_threat_model_locked"] = False
    session["blue_mitigations"] = []
    session["blue_mitigations_locked"] = False
# Red Team state
    session["red_attacks"] = []
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

    if session.get("current_team") != "red" or session.get("red_locked"):
        return redirect(url_for("home"))

    picks = []
    for i in range(1, game_data.ATTACKS_PER_GAME + 1):
        attack, _, target = request.form.get(f"attack_{i}", "").partition("|")
        picks.append({"attack": attack, "target": target})

    error = game_data.validate_red_attacks(picks)

    if error:
        flash(error)
        return redirect(url_for("home"))

    session["red_attacks"] = picks
    session["red_locked"] = True

    return redirect(url_for("home"))

@app.route("/blue-mitigations", methods=["POST"])
def blue_mitigations():
    if not session.get("game_started"):
        return redirect(url_for("home"))

    if (
        session.get("current_team") != "blue"
        or session.get("blue_step") != "mitigation"
        or session.get("blue_mitigations_locked")
    ):
        return redirect(url_for("home"))

    picks = []
    for value in request.form.getlist("pick"):
        mitigation, _, node = value.partition("|")
        picks.append({"mitigation": mitigation, "node": node})

    error = game_data.validate_blue_mitigations(
        picks,
        session["blue_budget"]
    )

    if error:
        flash(error)
        return redirect(url_for("home"))

    session["blue_mitigations"] = picks
    session["blue_mitigations_locked"] = True

    return redirect(url_for("home"))

@app.route("/end-turn", methods=["POST"])
def end_turn():
    if not session.get("game_started"):
        return redirect(url_for("home"))

    current_team = session["current_team"]

    if current_team == "blue" and session.get("blue_step") == "mitigation":
        # Blue must lock mitigations before the game is decided
        if not session.get("blue_mitigations_locked"):
            return redirect(url_for("home"))

        session["phase"] = "result"

    elif current_team == "blue":

        # Blue must lock the threat model before ending the turn
        if not session.get("blue_threat_model_locked"):
            return redirect(url_for("home"))

        session["next_team"] = "red"
        session["phase"] = "handover"

    else:
        # Red must make a choice before ending the turn
        if not session.get("red_locked"):
            return redirect(url_for("home"))

        # Blue picks mitigations next, in the same round
        session["blue_step"] = "mitigation"
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

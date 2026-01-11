from flask import Flask, request, render_template_string

app = Flask(__name__)

ACTIVITY_LEVELS = {
    "sedentary": ("Sedentary (little or no exercise)", 1.2),
    "light": ("Light (1–3 days/week)", 1.375),
    "moderate": ("Moderate (3–5 days/week)", 1.55),
    "active": ("Active (6–7 days/week)", 1.725),
    "very_active": ("Very active (hard exercise/physical job)", 1.9),
}

BMR_METHODS = {
    "mifflin": "Mifflin–St Jeor (default)",
    "harris": "Revised Harris–Benedict (1984)",
    "katch": "Katch–McArdle (uses body fat %)",
}

KJ_PER_KCAL = 4.184
LB_PER_KG = 2.2046226218
KCAL_PER_LB = 3500
KCAL_PER_DAY_PER_LB_PER_WEEK = KCAL_PER_LB / 7

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Calorie Calculator</title>
  <style>
    * { box-sizing: border-box; }

    :root { --bg:#0b0c10; --card:#111218; --text:#e9e9ee; --muted:#a9a9b3; --line:#242635; --accent:#7aa2ff; }
    body { margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
           background: radial-gradient(1200px 600px at 20% 0%, #14162a, var(--bg));
           color: var(--text); }
    .wrap { max-width: 920px; margin: 0 auto; padding: 28px 16px 50px; }
    h1 { font-size: 28px; margin: 6px 0 10px; }
    h2 { font-size: 18px; margin: 18px 0 10px; }
    p { margin: 0 0 18px; color: var(--muted); line-height: 1.45; }
    .card { background: rgba(17,18,24,.86); border:1px solid var(--line); border-radius: 16px; padding: 18px; }

    .grid { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 16px; }
    .grid > div { min-width: 0; }

    label { display:block; font-size: 13px; color: var(--muted); margin-bottom: 6px; }

    input, select {
      width:100%;
      display:block;
      padding: 10px 12px;
      border-radius: 12px;
      border:1px solid var(--line);
      background: #0f1016;
      color: var(--text);
      outline:none;
      line-height: 1.2;
    }

    input:focus, select:focus { border-color: rgba(122,162,255,.7); box-shadow: 0 0 0 3px rgba(122,162,255,.18); }
    .row { margin-top: 14px; }

    .btn {
      margin-top: 16px;
      width:100%;
      padding: 12px 14px;
      border-radius: 12px;
      border:1px solid var(--line);
      background: linear-gradient(180deg, rgba(122,162,255,.25), rgba(122,162,255,.10));
      color: var(--text);
      font-weight: 600;
      cursor: pointer;
    }
    .btn:hover { border-color: rgba(122,162,255,.7); }

    .results { margin-top: 16px; display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 16px; }
    .stat { border:1px solid var(--line); border-radius: 16px; padding: 14px; background: rgba(15,16,22,.75); }
    .stat .k { font-size: 13px; color: var(--muted); }
    .stat .v { font-size: 18px; margin-top: 6px; font-weight: 800; line-height: 1.25; }
    .stat .v small { font-weight: 600; color: var(--muted); }
    .stat .s { margin-top: 8px; font-size: 12px; color: var(--muted); line-height: 1.35; }

    .note { margin-top: 14px; font-size: 12px; color: var(--muted); line-height: 1.45; }
    .err { margin-top: 12px; color: #ffb4b4; }

    .divider { height: 1px; background: var(--line); margin: 18px 0; border-radius: 1px; opacity: 0.9; }
    .pill { display:inline-block; padding: 2px 8px; border: 1px solid var(--line); border-radius: 999px; font-size: 12px; color: var(--muted); }

    .checkrow { display:flex; align-items:center; gap:10px; margin-top: 12px; }
    .checkrow input[type="checkbox"] { width: 18px; height: 18px; margin: 0; }
    .checkrow span { color: var(--muted); font-size: 13px; }

    @media (max-width: 720px){
      .grid, .results { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Calorie Calculator</h1>
    <p>Choose a BMR method, enter your details, and get estimates for maintenance and weight loss targets.</p>

    <div class="card">
      <form method="post">
        <div class="grid">
          <div>
            <label for="age">Age (years)</label>
            <input id="age" name="age" type="number" min="10" max="120" step="1" required value="{{ vals.age }}">
          </div>
          <div>
            <label for="sex">Sex</label>
            <select id="sex" name="sex" required>
              <option value="male" {{ "selected" if vals.sex=="male" else "" }}>Male</option>
              <option value="female" {{ "selected" if vals.sex=="female" else "" }}>Female</option>
            </select>
          </div>
          <div>
            <label for="height_cm">Height (cm)</label>
            <input id="height_cm" name="height_cm" type="number" min="90" max="250" step="0.1" required value="{{ vals.height_cm }}">
          </div>
          <div>
            <label for="weight_kg">Weight (kg)</label>
            <input id="weight_kg" name="weight_kg" type="number" min="25" max="400" step="0.1" required value="{{ vals.weight_kg }}">
          </div>
        </div>

        <div class="grid row">
          <div>
            <label for="bmr_method">BMR / RDEE method</label>
            <select id="bmr_method" name="bmr_method" required onchange="toggleBodyFat()">
              {% for key, label in bmr_methods.items() %}
                <option value="{{ key }}" {{ "selected" if vals.bmr_method==key else "" }}>{{ label }}</option>
              {% endfor %}
            </select>
          </div>
          <div>
            <label for="activity">Workout frequency</label>
            <select id="activity" name="activity" required>
              {% for key, (label, _) in activity_levels.items() %}
                <option value="{{ key }}" {{ "selected" if vals.activity==key else "" }}>{{ label }}</option>
              {% endfor %}
            </select>
          </div>
        </div>

        <div class="row" id="bodyfat_row" style="display:none;">
          <label for="bodyfat">Body fat % (only for Katch–McArdle)</label>
          <input id="bodyfat" name="bodyfat" type="number" min="2" max="70" step="0.1" value="{{ vals.bodyfat }}" placeholder="e.g., 15">
        </div>

        <div class="checkrow">
          <input id="cap_deficit" name="cap_deficit" type="checkbox" value="1" {{ "checked" if vals.cap_deficit else "" }}>
          <span>Apply 1000 kcal/day deficit cap (optional safety)</span>
        </div>

        <input type="hidden" name="action" value="calculate" />
        <button class="btn" type="submit">Calculate</button>

        {% if error %}
          <div class="err">{{ error }}</div>
        {% endif %}
      </form>

      {% if results %}
        <div class="results">
          <div class="stat">
            <div class="k">Maintain Weight <span class="pill">TDEE</span></div>
            <div class="v">{{ results.maintain_kcal }} kcal/day <small>({{ results.maintain_kj }} kJ/day)</small></div>
            <div class="s">BMR/RDEE: {{ results.bmr_kcal }} kcal/day ({{ results.bmr_method_label }})</div>
          </div>

          <div class="stat">
            <div class="k">Mild weight loss</div>
            <div class="v">{{ results.mild_kcal }} kcal/day <small>({{ results.mild_kj }} kJ/day)</small></div>
            <div class="s">Target ~0.25 kg/week • Deficit ~{{ results.mild_def }} kcal/day</div>
          </div>

          <div class="stat">
            <div class="k">Weight loss</div>
            <div class="v">{{ results.loss_kcal }} kcal/day <small>({{ results.loss_kj }} kJ/day)</small></div>
            <div class="s">Target ~0.5 kg/week • Deficit ~{{ results.loss_def }} kcal/day</div>
          </div>

          <div class="stat">
            <div class="k">Extreme weight loss</div>
            <div class="v">{{ results.extreme_kcal }} kcal/day <small>({{ results.extreme_kj }} kJ/day)</small></div>
            <div class="s">Target ~1 kg/week • Deficit ~{{ results.extreme_def }} kcal/day{% if results.deficit_capped %} (capped){% endif %}</div>
          </div>
        </div>

        <div class="note">
          Weight-loss deficits follow the “3500 kcal per lb” rule-of-thumb:
          ~500 kcal/day ≈ 1 lb/week. Results are estimates; consult a professional for medical guidance.
        </div>
      {% endif %}

      <div class="divider"></div>

      <h2>kcal ↔ kJ Converter</h2>
      <p>Convert calories (kcal) to kilojoules (kJ), or the other way around.</p>

      <form method="post">
        <div class="grid">
          <div>
            <label for="conv_value">Value</label>
            <input id="conv_value" name="conv_value" type="number" step="0.01" min="0" required value="{{ conv.val }}">
          </div>
          <div>
            <label for="conv_direction">Convert</label>
            <select id="conv_direction" name="conv_direction" required>
              <option value="kcal_to_kj" {{ "selected" if conv.dir=="kcal_to_kj" else "" }}>kcal → kJ</option>
              <option value="kj_to_kcal" {{ "selected" if conv.dir=="kj_to_kcal" else "" }}>kJ → kcal</option>
            </select>
          </div>
        </div>

        <input type="hidden" name="action" value="convert" />
        <button class="btn" type="submit">Convert</button>

        {% if conv_result %}
          <div class="results" style="grid-template-columns: 1fr; margin-top: 12px;">
            <div class="stat">
              <div class="k">Result</div>
              <div class="v">{{ conv_result }}</div>
              <div class="s">Using 1 kcal = 4.184 kJ</div>
            </div>
          </div>
        {% endif %}

        {% if conv_error %}
          <div class="err">{{ conv_error }}</div>
        {% endif %}
      </form>
    </div>
  </div>

  <script>
    function toggleBodyFat(){
      const method = document.getElementById("bmr_method").value;
      const row = document.getElementById("bodyfat_row");
      row.style.display = (method === "katch") ? "block" : "none";
    }
    toggleBodyFat();
  </script>
</body>
</html>
"""

def rint(x):
    return int(round(x))

def kcal_to_kj(kcal):
    return kcal * KJ_PER_KCAL

def kj_to_kcal(kj):
    return kj / KJ_PER_KCAL

def safe_intake_floor(sex):
    return 1500 if sex == "male" else 1200

def bmr_mifflin(sex, age, h, w):
    return 10*w + 6.25*h - 5*age + (5 if sex=="male" else -161)

def bmr_harris(sex, age, h, w):
    return (13.397*w + 4.799*h - 5.677*age + 88.362) if sex=="male" else (9.247*w + 3.098*h - 4.33*age + 447.593)

def bmr_katch(w, bf):
    return 370 + 21.6*(1-bf/100)*w

def deficit_from_kg(kg):
    return rint(kg * LB_PER_KG * KCAL_PER_DAY_PER_LB_PER_WEEK)

@app.route("/", methods=["GET","POST"])
def index():
    vals={"age":"","sex":"male","height_cm":"","weight_kg":"","activity":"moderate","bmr_method":"mifflin","bodyfat":""}
    conv={"val":"","dir":"kcal_to_kj"}
    results=None
    conv_result=None

    if request.method=="POST":
        if request.form.get("action")=="calculate":
            age=float(request.form["age"])
            h=float(request.form["height_cm"])
            w=float(request.form["weight_kg"])
            sex=request.form["sex"]
            act=request.form["activity"]
            method=request.form["bmr_method"]
            bf=request.form.get("bodyfat","")

            if method=="mifflin":
                bmr=bmr_mifflin(sex,age,h,w)
            elif method=="harris":
                bmr=bmr_harris(sex,age,h,w)
            else:
                bmr=bmr_katch(w,float(bf))

            tdee=bmr*ACTIVITY_LEVELS[act][1]

            mild=tdee-deficit_from_kg(0.25)
            loss=tdee-deficit_from_kg(0.5)
            extreme=tdee-deficit_from_kg(1.0)

            f=safe_intake_floor(sex)

            results={
                "maintain_kcal":rint(tdee),
                "maintain_kj":rint(kcal_to_kj(tdee)),
                "mild_kcal":rint(max(mild,f)),
                "mild_kj":rint(kcal_to_kj(max(mild,f))),
                "loss_kcal":rint(max(loss,f)),
                "loss_kj":rint(kcal_to_kj(max(loss,f))),
                "extreme_kcal":rint(max(extreme,f)),
                "extreme_kj":rint(kcal_to_kj(max(extreme,f)))
            }

        else:
            v=float(request.form["conv_value"])
            d=request.form["conv_direction"]
            conv["val"]=v
            conv["dir"]=d
            conv_result=f"{v} kcal = {kcal_to_kj(v):.2f} kJ" if d=="kcal_to_kj" else f"{v} kJ = {kj_to_kcal(v):.2f} kcal"

    return render_template_string(PAGE,activity_levels=ACTIVITY_LEVELS,bmr_methods=BMR_METHODS,vals=vals,results=results,conv=conv,conv_result=conv_result)

if __name__=="__main__":
    app.run(debug=True)
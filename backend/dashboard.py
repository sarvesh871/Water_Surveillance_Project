from datetime import datetime
from config import COLLECTION_INTERVAL
from mode_state import get_mode
from storage import get_recent, get_history
from config import STALE_AFTER_SECONDS
from html import escape

def get_water_level(value):
       return "Detected" if value else "Not Detected"


def get_light_status(light):
       if light > 80:
           return "Bright"
       elif light > 30:
           return "Moderate"
       return "Dark"


def get_ph_status(ph):
       if 6.5 <= ph <= 8.5:
           return "✅ Safe", "#2ecc71"
       return "⚠ Outside Safe Range", "#e74c3c"


def get_temp_status(temp):
       if 15 <= temp <= 35:
           return "✅ Normal", "#2ecc71"
       return "⚠ Check", "#f39c12"

def get_turbidity_status(turbidity):
       if turbidity <= 5:
           return "✅ Clear", "#2ecc71"
       return "⚠ High", "#e74c3c"


def get_risk_colour(level):
       colours = {
           "Very Low":"#2ecc71",
           "Low":"#27ae60",
           "Moderate":"#f1c40f",
           "High":"#e67e22",
           "Critical":"#e74c3c"
       }
       return colours.get(level, "#7f8c8d")


def _sparkline(rows, key, title, unit, color, width=760, height=150):
       """Build a small dependency-free SVG chart from recent stored rows."""
       values = []
       for row in rows:
           try:
               value = float(row.get(key))
               if value == value and abs(value) != float("inf"):
                   values.append((row.get("timestamp", ""), value))
           except (TypeError, ValueError):
               continue
       if len(values) < 2:
           return f"<section class='chart'><h3>{escape(title)}</h3><p>Not enough valid readings yet.</p></section>"
       vals = [item[1] for item in values]
       low, high = min(vals), max(vals)
       if high == low:
           high = low + 1
       pad_x, pad_y = 28, 18
       plot_w, plot_h = width - 2 * pad_x, height - 2 * pad_y
       points = []
       for i, value in enumerate(vals):
           x = pad_x + (i / (len(vals)-1)) * plot_w
           y = height - pad_y - ((value-low)/(high-low))*plot_h
           points.append(f"{x:.1f},{y:.1f}")
       polyline = " ".join(points)
       labels = f"<text x='{pad_x}' y='{height-2}' font-size='10' fill='#687782'>{low:.2f} {escape(unit)}</text><text x='{width-pad_x}' y='{height-2}' text-anchor='end' font-size='10' fill='#687782'>{high:.2f} {escape(unit)}</text>"
       return f"""<section class='chart'><h3>{escape(title)}</h3>
       <svg viewBox='0 0 {width} {height}' role='img' aria-label='{escape(title)} history chart'>
         <line x1='{pad_x}' y1='{height-pad_y}' x2='{width-pad_x}' y2='{height-pad_y}' stroke='#d7e0e7'/>
         <line x1='{pad_x}' y1='{pad_y}' x2='{pad_x}' y2='{height-pad_y}' stroke='#d7e0e7'/>
         <polyline points='{polyline}' fill='none' stroke='{color}' stroke-width='3' stroke-linejoin='round' stroke-linecap='round'/>
         {labels}
       </svg><p class='chart-meta'>Last {len(values)} stored readings · values shown in {escape(unit)}</p></section>"""

def render(reading, last_error=None, last_success_at=None):

       if not reading:
           return """
           <html>
           <head>
           <meta http-equiv="refresh" content="10">
           <style>
           body{
               font-family:Arial;
               background:#f5f7fa;
               text-align:center;
               padding-top:100px;
           }
           
</style>
           </head>
           <body>
           <h1>IoT Based Smart Water Quality Monitoring and Disease Prediction System</h1>
           <h3>Waiting for Readings...</h3>
           <form method="post" action="/mode" style="margin-top:20px;">
               <button type="submit" name="mode" value="SENSOR">Use ESP32 Sensors</button>
               <button type="submit" name="mode" value="SIMULATED">Use Simulated Readings</button>
           </form>
           </body>
           </html>
           """

       ph_status, ph_color = get_ph_status(reading["ph"])
       temp_status, temp_color = get_temp_status(reading["temp"])
       turb_status, turb_color = get_turbidity_status(reading["turbidity"])
       validation_status = reading.get("validation_status", "UNKNOWN")
       reasons = reading.get("prediction_reasons", [])

       status_colors = {
           "VALID": "#27ae60",
           "NEEDS_ATTENTION": "#f39c12",
           "NON_POTABLE": "#c0392b",
           "SENSOR_ERROR": "#8e44ad",
           "UNKNOWN": "#7f8c8d"
       }

       validation_color = status_colors.get(validation_status, "#7f8c8d")

       if reasons:
           reasons_html = "".join(
               f"<li>{escape(str(reason))}</li>"
               for reason in reasons
           )
           reasons_html = f"<ul style='text-align:left;'>{reasons_html}</ul>"
       else:
           reasons_html = (
               "<p>No screening violations detected.</p>"
               if validation_status == "VALID"
               else "<p>Validation details unavailable.</p>"
           )
       prediction_color = "#27ae60"

       current_mode = get_mode()
       mode_label = "Simulated readings" if current_mode == "SIMULATED" else "ESP32 sensor readings"
       source_label = escape(str(reading.get("data_source", current_mode)))
       sample_label = escape(str(reading.get("sample_type", "Unknown")))
       recent = get_recent()

       recent_rows = ""
       for row in recent:
           recent_rows += f"""
           <tr>
               <td>{escape(str(row.get('timestamp') or '—'))}</td>
               <td>{escape(str(row.get('ph') if row.get('ph') is not None else '—'))}</td>
               <td>{escape(str(row.get('temp') if row.get('temp') is not None else '—'))} °C</td>
               <td>{escape(str(row.get('turbidity') if row.get('turbidity') is not None else '—'))}</td>
               <td>{escape(str(row.get('tds') if row.get('tds') is not None else '—'))} ppm</td>
               <td style="font-weight:bold; color:{'#27ae60' if row.get('prediction')=='Potable' else '#c0392b'}">
               {escape(str(row.get('prediction') or '—'))}
               </td>
           </tr>
           """

       history = get_history(60)
       sensor_status = "● Data current" if last_success_at and not last_error else "● Data unavailable / collection error"
       sensor_status_color = "#27ae60" if last_success_at and not last_error else "#c0392b"
       error_banner = f"<div class='error-banner'>Latest collection error: {escape(str(last_error))}</div>" if last_error else ""

       prediction_colors = {
           "Potable": "#27ae60",
           "Non-Potable": "#c0392b",
           "Needs Attention": "#f39c12",
           "Sensor Error": "#8e44ad"
       }

       prediction_color = prediction_colors.get(
           reading["prediction"], "#7f8c8d"
       )
       risk_colour = get_risk_colour(reading["risk_level"])

       return f"""
<html>
<head>
<meta http-equiv="refresh" content="{COLLECTION_INTERVAL}">
<title>Water Quality Dashboard</title>
<style>

body{{
       background:#eef3f7;
       font-family:Arial,Helvetica,sans-serif;
       margin:0;
}}

.container{{
       width:min(1200px, calc(100% - 32px));
       margin:24px auto;
}}

.card{{
       background:white;
       border-radius:15px;
       padding:30px;
       box-shadow:0px 8px 25px rgba(0,0,0,.15);
}}

table{{
       width:100%;
       border-collapse:collapse;
       margin-top:15px;
}}

.chart-grid{{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(300px,1fr));
    gap:16px;
    margin-top:18px;
}}
.chart{{
    background:#fff;
    border:1px solid #e0e7ed;
    border-radius:10px;
    padding:14px;
    min-width:0;
}}
.chart h3{{margin:0 0 8px;color:#2c3e50;font-size:18px;}}
.chart svg{{width:100%;height:auto;display:block;}}
.chart-meta{{font-size:12px;color:#687782;margin:5px 0 0;}}
.table-wrap{{overflow-x:auto;}}

th{{
       text-align:center;
       background:#3498db;
       color:white;
       padding:12px;
}}

td{{
       text-align:center;
       padding:12px;
       border-bottom:1px solid #ddd;
}}

h1{{
       text-align:center;
       color:#2c3e50;
}}

h2{{
       color:#2c3e50;
       margin-top:35px;
}}


.prediction{{
       margin-top:25px;
       padding:18px;
       border-radius:10px;
       background:#f7f7f7;
       text-align:center;
       font-size:30px;
       font-weight:bold;
}}

.footer{{
       text-align:center;
       margin-top:20px;
       color:gray;
}}

.status{{
       font-weight:bold;
       color:#27ae60;
       text-align:right;
}}

@media (max-width: 640px){{
    .card{{padding:16px;}}
    .container{{width:calc(100% - 16px);margin:8px auto;}}
    .chart-grid{{grid-template-columns:1fr;}}
    .prediction{{font-size:22px;}}
    th,td{{padding:8px;font-size:13px;}}
}}
</style>
</head>
<body>
<div class="container">
<div class="card">
<h1>IoT Based Smart Water Quality Monitoring and Disease Prediction System</h1>
<p class="status">
{sensor_status}
</p>
{error_banner}
<div style="margin:18px 0;padding:16px;background:#f7f7f7;border-radius:10px;text-align:center;">
<strong>Reading mode: {mode_label}</strong>
<form method="post" action="/mode" style="margin-top:12px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
<button type="submit" name="mode" value="SENSOR" style="padding:10px 16px;border:0;border-radius:6px;background:{'#2471a3' if current_mode == 'SENSOR' else '#bdc3c7'};color:white;cursor:pointer;">Use ESP32 Sensors</button>
<button type="submit" name="mode" value="SIMULATED" style="padding:10px 16px;border:0;border-radius:6px;background:{'#2471a3' if current_mode == 'SIMULATED' else '#bdc3c7'};color:white;cursor:pointer;">Use Simulated Readings</button>
</form>
<p style="font-size:13px;color:#666;margin-bottom:0;">Mode changes apply to the next scheduled reading. Simulated values are not real measurements. Hardware turbidity may be demo-adjusted; the raw signal is retained for transparency.</p>
</div>

<table>
<tr>
<td class="label">Last Updated</td>
<td>{reading["timestamp"]}</td>
</tr>
<tr><td class="label">Reading Source</td><td>{source_label}</td></tr>
<tr><td class="label">Sample Scenario</td><td>{sample_label}</td></tr>
<tr>
<td class="label">Sensor Status</td>
<td style="color:green;">
● All Sensors Active
</td>
</tr>
<tr>
<td class="label">pH</td>
<td>{reading["ph"]} &nbsp;&nbsp;
<span style="color:{ph_color}">
{ph_status}
</span>
</td>
</tr>
<tr>
<td class="label">Temperature</td>
<td>{reading["temp"]} °C &nbsp;&nbsp;
<span style="color:{temp_color}">
{temp_status}
</span>
</td>
</tr>
<tr>
<td class="label">Turbidity</td>
<td>{reading["turbidity"]} {"demo-adjusted value" if reading.get("data_source") == "SENSOR" and reading.get("turbidity_adjusted") else "NTU"} &nbsp;&nbsp;
<span style="color:{turb_color}">
{turb_status}
</span>
</td>
</tr>
<tr>
<td class="label">Raw turbidity signal</td>
<td>{reading.get("turbidity_raw", "Not applicable")}</td>
</tr>
<tr>
<td class="label">Turbidity adjustment</td>
<td>{"Applied for demonstration; not a calibrated NTU measurement" if reading.get("turbidity_adjusted") else "Not applied"}</td>
</tr>
<tr>
<td class="label">TDS</td>
<td>{reading["tds"]} ppm</td>
</tr>
<tr>
<td class="label">Water Level</td>
<td>{get_water_level(reading["water"])}</td>
</tr>
<tr>
<td class="label">Light</td>
<td>{reading["light"]} ({get_light_status(reading["light"])})</td>
</tr>
</table>

<br>
<div class="prediction">
Current Water Quality
<br><br>
<span style="color:{prediction_color};">
{reading["prediction"]}
</span>
</div>

<div class="prediction">
Water Quality Validation Report
<br><br>

Validation Status:
<span style="color:{validation_color};font-weight:bold;">
{validation_status.replace("_", " ")}
</span>
<br><br>

<div style="font-size:15px;">
{reasons_html}
</div>

</div>

<div class="prediction">
Disease Risk Assessment
<br><br>
Risk Score :
<b>{reading["risk_score"]}</b>
<br><br>
Risk Level :
<span style="color:{risk_colour};font-size:26px;font-weight:bold;">
{reading["risk_level"]}
</span>
<br><br>
Expected Cases :
<b>{reading["expected_cases"]}</b>
</div>

<h2>Recent Trends</h2>
<p style="color:#687782;font-size:14px;">Charts use the latest stored history. Adjusted hardware turbidity is a demonstration value, not calibrated NTU.</p>
<div class="chart-grid">
{_sparkline(history, "ph", "pH trend", "pH", "#2980b9")}
{_sparkline(history, "tds", "TDS trend", "ppm", "#16a085")}
{_sparkline(history, "turbidity", "Turbidity trend", "pipeline units", "#d35400")}
{_sparkline(history, "temp", "Temperature trend", "°C", "#8e44ad")}
{_sparkline(history, "risk_score", "Experimental risk index", "0–1 index", "#c0392b")}
</div>

<h2>Recent Readings</h2>
<table>
<tr>
<th>Time</th>
<th>pH</th>
<th>Temp</th>
<th>Turbidity</th>
<th>TDS (ppm)</th>
<th>Prediction</th>
</tr>
{recent_rows}
</table>
<div class="footer">
Automatically updating every {COLLECTION_INTERVAL} seconds
</div>
</div>
</div>
</body>
</html>
"""
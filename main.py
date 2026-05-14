# ================================
# FILE: main.py
# ================================

import pandas as pd
import sqlite3
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -------------------------------
# STEP 1: READ CSV FILES
# -------------------------------
try:

    runtime = pd.read_csv("runtime.csv")
    production = pd.read_csv("production.csv")
    downtime = pd.read_csv("downtime.csv")

except Exception as e:

    print("Error reading CSV files:", e)
    exit()

# -------------------------------
# STEP 2: EXTRACT VALUES
# -------------------------------
try:

    run_time = runtime.iloc[0]["run_time"]
    planned_time = runtime.iloc[0]["planned_time"]

    total_units = production.iloc[0]["total_units"]
    good_units = production.iloc[0]["good_units"]
    ideal_cycle_time = production.iloc[0]["ideal_cycle_time"]

except Exception as e:

    print("CSV column error:", e)
    exit()

# -------------------------------
# STEP 3: CALCULATE OEE
# -------------------------------
availability = (run_time / planned_time) * 100

performance = (
    (ideal_cycle_time * total_units)
    / run_time
) * 100

quality = (good_units / total_units) * 100

oee = (
    availability
    * performance
    * quality
) / 10000

# -------------------------------
# STEP 4: DOWNTIME ANALYSIS
# -------------------------------
total_downtime = downtime["minutes"].sum()

top_downtime = downtime.sort_values(
    by="minutes",
    ascending=False
).head(3)

# -------------------------------
# STEP 5: OEE STATUS
# -------------------------------
if oee >= 85:

    status = "Excellent"
    status_color = "#16a34a"

elif oee >= 60:

    status = "Average"
    status_color = "#f59e0b"

else:

    status = "Poor"
    status_color = "#dc2626"

# -------------------------------
# STEP 6: STORE INTO DATABASE
# -------------------------------
conn = sqlite3.connect("oee.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS oee_report (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    availability REAL,
    performance REAL,
    quality REAL,
    oee REAL,
    timestamp TEXT

)
""")

cursor.execute("""
INSERT INTO oee_report
(availability, performance, quality, oee, timestamp)

VALUES (?, ?, ?, ?, ?)
""", (

    availability,
    performance,
    quality,
    oee,
    datetime.now().strftime("%d-%m-%Y %H:%M")

))

conn.commit()
conn.close()

# -------------------------------
# STEP 7: TERMINAL OUTPUT
# -------------------------------
print("\n========== OEE REPORT ==========\n")

print("Availability :", round(availability, 2), "%")
print("Performance  :", round(performance, 2), "%")
print("Quality      :", round(quality, 2), "%")
print("Final OEE    :", round(oee, 2), "%")

print("\nTop Downtime Reasons:")

print(top_downtime)
# -------------------------------
# STEP 8: EMAIL-SAFE HTML REPORT
# -------------------------------
current_time = datetime.now().strftime("%d-%m-%Y %H:%M")

# Use a hex color for the status background based on your logic
status_bg = "#fbbf24" if status == "Average" else "#10b981" # Example logic

with open("report.html", "w", encoding="utf-8") as f:
    f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Industrial OEE Report</title>
</head>
<body style="margin:0; padding:20px; background-color:#030712; font-family: 'Segoe UI', Helvetica, Arial, sans-serif; color:#f8fafc;">
    <div style="max-width:600px; margin:0 auto; background-color:#111827; border-radius:16px; overflow:hidden; border:1px solid #1f2937;">
        
        <!-- Header -->
        <table width="100%" cellpadding="0" cellspacing="0" style="padding:30px; border-bottom:1px solid #1f2937;">
            <tr>
                <td>
                    <h1 style="margin:0; font-size:20px; letter-spacing:1px; color:#ffffff;">OEE<span style="color:#38bdf8;">CORE</span> ANALYTICS</h1>
                    <p style="margin:5px 0 0 0; font-size:12px; color:#94a3b8;">LAST UPDATED: {current_time}</p>
                </td>
                <td align="right">
                    <span style="background-color:rgba(251,191,36,0.1); border:1px solid {status_bg}; color:{status_bg}; padding:5px 12px; border-radius:20px; font-size:11px; font-weight:bold; text-transform:uppercase;">
                        ● {status}
                    </span>
                </td>
            </tr>
        </table>

        <!-- Hero OEE Score -->
        <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 30px; background:linear-gradient(to bottom right, #111827, #1e1b4b);">
            <tr>
                <td>
                    <p style="margin:0; font-size:13px; color:#94a3b8; font-weight:bold; text-transform:uppercase;">Overall Effectiveness</p>
                    <h2 style="margin:10px 0; font-size:64px; color:#f43f5e; line-height:1;">{oee:.1f}%</h2>
                    <p style="margin:0; font-size:14px; color:#64748b;">Total Manufacturing Health Score</p>
                </td>
                <td align="right" valign="bottom">
                    <p style="margin:0; font-size:11px; color:#94a3b8;">BENCHMARK</p>
                    <p style="margin:0; font-size:20px; font-weight:bold; color:#ffffff;">85.0%</p>
                </td>
            </tr>
        </table>

        <!-- Metrics Grid (Using Table for Email Compatibility) -->
        <table width="100%" cellpadding="0" cellspacing="0" style="padding:20px 30px;">
            <tr>
                <td width="50%" style="padding:10px; background-color:#1f2937; border-radius:12px; border:1px solid #374151;">
                    <p style="margin:0; font-size:11px; color:#94a3b8; font-weight:bold;">AVAILABILITY</p>
                    <p style="margin:5px 0; font-size:24px; color:#38bdf8; font-weight:bold;">{availability:.1f}%</p>
                </td>
                <td width="10px"></td> <!-- Spacer -->
                <td width="50%" style="padding:10px; background-color:#1f2937; border-radius:12px; border:1px solid #374151;">
                    <p style="margin:0; font-size:11px; color:#94a3b8; font-weight:bold;">PERFORMANCE</p>
                    <p style="margin:5px 0; font-size:24px; color:#fbbf24; font-weight:bold;">{performance:.1f}%</p>
                </td>
            </tr>
            <tr><td height="10px"></td></tr>
            <tr>
                <td width="50%" style="padding:10px; background-color:#1f2937; border-radius:12px; border:1px solid #374151;">
                    <p style="margin:0; font-size:11px; color:#94a3b8; font-weight:bold;">QUALITY</p>
                    <p style="margin:5px 0; font-size:24px; color:#10b981; font-weight:bold;">{quality:.1f}%</p>
                </td>
                <td width="10px"></td>
                <td width="50%" style="padding:20px; border-radius:12px; border:1px dashed #374151; text-align:center;">
                    <p style="margin:0; font-size:11px; color:#64748b;">SYSTEM STATUS</p>
                    <p style="margin:5px 0; font-size:14px; color:#ffffff; font-weight:bold;">ACTIVE</p>
                </td>
            </tr>
        </table>

        <!-- Insights Footer -->
        <div style="padding:20px 30px; background-color:#0f172a; font-size:13px; color:#94a3b8; line-height:1.6; text-align:center;">
            OEE is currently <strong>{status}</strong>. {total_downtime} total minutes lost recorded.
            <br>
            <span style="font-size:11px; margin-top:10px; display:block;">© 2026 Industrial Intelligence Systems</span>
        </div>
    </div>
</body>
</html>
""")

# -------------------------------
# STEP 9: SEND EMAIL
# -------------------------------
sender_email = "gonapalikhitha@gmail.com"

receiver_email = "likhithagonapa19@gmail.com"

app_password = "lbjphjedfqpshvjl"

message = MIMEMultipart("alternative")

message["Subject"] = "Daily OEE Report"

message["From"] = sender_email

message["To"] = receiver_email

with open("report.html", "r", encoding="utf-8") as f:

    html_content = f.read()

message.attach(MIMEText(html_content, "html"))

try:

    server = smtplib.SMTP("smtp.gmail.com", 587)

    server.starttls()

    server.login(sender_email, app_password)

    server.sendmail(
        sender_email,
        receiver_email,
        message.as_string()
    )

    server.quit()

    print("\nEmail Sent Successfully!")

except Exception as e:

    print("\nEmail Error:", e)
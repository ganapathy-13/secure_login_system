from flask import Flask, render_template
import sqlite3
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

DB_PATH = 'users.db'
CHART_PATH = 'static/donut_chart.png'

# Get count of each login status from login_logs
def get_login_status_counts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT status, COUNT(*) 
        FROM login_logs 
        GROUP BY status
    """)
    
    rows = cursor.fetchall()
    conn.close()

    labels = [row[0].capitalize() for row in rows]
    data = [row[1] for row in rows]
    
    return data, labels

# Generate donut chart and save as image
def generate_donut_chart(data, labels, filename="static/donut_chart.png"):
    # Set figure size and style
    fig, ax = plt.subplots(figsize=(6, 6))  # square aspect for perfect circle
    
    # Pie chart with donut effect
    wedges, texts, autotexts = ax.pie(
        data,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor='w')  # donut with white edge
    )
    
    # Draw white circle in the middle
    centre_circle = plt.Circle((0, 0), 0.55, fc='white')
    fig.gca().add_artist(centre_circle)

    # Equal aspect ratio = perfectly circular
    ax.axis('equal')  
    
    # Save the chart
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


@app.route('/')
def dashboard():
    data, labels = get_login_status_counts()
    generate_donut_chart(data, labels)
    return render_template('dashboard.html', chart_url='/' + CHART_PATH)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True)

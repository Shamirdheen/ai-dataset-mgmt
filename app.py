from flask import Flask, render_template, request, redirect, url_for
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)

def get_db():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(database_url)

# ---------- DASHBOARD ----------
@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT COUNT(*) FROM datasets")
    dataset_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM dataset_versions")
    version_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM annotations")
    annotation_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    cur.execute("""
        SELECT d.name, u.name AS created_by, COUNT(dv.version_id) AS total_versions
        FROM datasets d
        JOIN users u ON d.created_by = u.user_id
        LEFT JOIN dataset_versions dv ON d.dataset_id = dv.dataset_id
        GROUP BY d.dataset_id, u.name
    """)
    datasets = cur.fetchall()
    cur.close(); conn.close()
    return render_template("index.html",
        dataset_count=dataset_count,
        version_count=version_count,
        annotation_count=annotation_count,
        user_count=user_count,
        datasets=datasets)

# ---------- DATASETS ----------
@app.route("/datasets")
def datasets():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT d.*, u.name AS creator
        FROM datasets d JOIN users u ON d.created_by = u.user_id
        ORDER BY d.created_at DESC
    """)
    datasets = cur.fetchall()
    cur.execute("SELECT user_id, name FROM users")
    users = cur.fetchall()
    cur.close(); conn.close()
    return render_template("datasets.html", datasets=datasets, users=users)

@app.route("/datasets/add", methods=["POST"])
def add_dataset():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO datasets (name, description, domain, format, source, created_by)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (request.form["name"], request.form["description"],
          request.form["domain"], request.form["format"],
          request.form["source"], request.form["created_by"]))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for("datasets"))

@app.route("/datasets/delete/<int:dataset_id>")
def delete_dataset(dataset_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM datasets WHERE dataset_id = %s", (dataset_id,))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for("datasets"))

# ---------- VERSIONS ----------
@app.route("/versions")
def versions():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT dv.*, d.name AS dataset_name
        FROM dataset_versions dv JOIN datasets d ON dv.dataset_id = d.dataset_id
        ORDER BY dv.created_at DESC
    """)
    versions = cur.fetchall()
    cur.execute("SELECT dataset_id, name FROM datasets")
    datasets = cur.fetchall()
    cur.close(); conn.close()
    return render_template("versions.html", versions=versions, datasets=datasets)

@app.route("/versions/add", methods=["POST"])
def add_version():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO dataset_versions (dataset_id, version_tag, changelog, file_size_mb, total_samples)
        VALUES (%s, %s, %s, %s, %s)
    """, (request.form["dataset_id"], request.form["version_tag"],
          request.form["changelog"], request.form["file_size_mb"],
          request.form["total_samples"]))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for("versions"))

# ---------- ANNOTATIONS ----------
@app.route("/annotations")
def annotations():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT a.*, u.name AS annotator, dv.version_tag
        FROM annotations a
        JOIN users u ON a.annotated_by = u.user_id
        JOIN dataset_versions dv ON a.version_id = dv.version_id
        ORDER BY a.annotated_at DESC
    """)
    annotations = cur.fetchall()
    cur.execute("SELECT version_id, version_tag FROM dataset_versions")
    versions = cur.fetchall()
    cur.execute("SELECT user_id, name FROM users")
    users = cur.fetchall()
    cur.close(); conn.close()
    return render_template("annotations.html", annotations=annotations, versions=versions, users=users)

@app.route("/annotations/add", methods=["POST"])
def add_annotation():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO annotations (version_id, annotated_by, sample_id, label, status)
        VALUES (%s, %s, %s, %s, %s)
    """, (request.form["version_id"], request.form["annotated_by"],
          request.form["sample_id"], request.form["label"], request.form["status"]))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for("annotations"))

# ---------- USERS ----------
@app.route("/users")
def users():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT u.user_id, u.name, u.email, u.created_at,
               STRING_AGG(r.role_name, ', ') AS roles
        FROM users u
        LEFT JOIN user_roles ur ON u.user_id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.role_id
        GROUP BY u.user_id, u.name, u.email, u.created_at
    """)
    users = cur.fetchall()
    cur.execute("SELECT role_id, role_name FROM roles")
    roles = cur.fetchall()
    cur.close(); conn.close()
    return render_template("users.html", users=users, roles=roles)

@app.route("/users/add", methods=["POST"])
def add_user():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)
        RETURNING user_id
    """, (request.form["name"], request.form["email"], "hashed_pw"))
    user_id = cur.fetchone()[0]
    cur.execute("INSERT INTO user_roles VALUES (%s, %s, NOW())",
                (user_id, request.form["role_id"]))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for("users"))

# ---------- SCORES ----------
@app.route("/scores")
def scores():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT dvs.*, dv.version_tag, d.name AS dataset_name
        FROM dataset_version_scores dvs
        JOIN dataset_versions dv ON dvs.version_id = dv.version_id
        JOIN datasets d ON dv.dataset_id = d.dataset_id
        ORDER BY dvs.overall_score DESC
    """)
    scores = cur.fetchall()
    cur.execute("""
        SELECT dsi.*, dvs.version_id
        FROM dataset_score_issues dsi
        JOIN dataset_version_scores dvs ON dsi.score_id = dvs.score_id
    """)
    issues = cur.fetchall()
    cur.close(); conn.close()
    return render_template("scores.html", scores=scores, issues=issues)

# ---------- INIT DB ----------
@app.route('/init-db')
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(open('schema.sql', 'r').read())
    conn.commit()
    cur.close()
    conn.close()
    return "Database initialized successfully!"
# ---------- SHOWCASE QUERIES ----------
@app.route("/queries")
def queries():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Query 1: Datasets with creator
    cur.execute("""
        SELECT d.name, d.domain, d.format, u.name AS created_by
        FROM datasets d
        JOIN users u ON d.created_by = u.user_id
    """)
    q1 = cur.fetchall()

    # Query 2: Versions with sample count
    cur.execute("""
        SELECT d.name AS dataset, dv.version_tag, dv.total_samples, dv.file_size_mb
        FROM dataset_versions dv
        JOIN datasets d ON dv.dataset_id = d.dataset_id
        ORDER BY dv.total_samples DESC
    """)
    q2 = cur.fetchall()

    # Query 3: Annotations with annotator
    cur.execute("""
        SELECT a.sample_id, a.label, a.status, u.name AS annotator
        FROM annotations a
        JOIN users u ON a.annotated_by = u.user_id
    """)
    q3 = cur.fetchall()

    # Query 4: Quality scores per version
    cur.execute("""
        SELECT d.name AS dataset, dv.version_tag, dvs.overall_score,
               dvs.completeness_score, dvs.consistency_score
        FROM dataset_version_scores dvs
        JOIN dataset_versions dv ON dvs.version_id = dv.version_id
        JOIN datasets d ON dv.dataset_id = d.dataset_id
        ORDER BY dvs.overall_score DESC
    """)
    q4 = cur.fetchall()

    # Query 5: Score issues with severity
    cur.execute("""
        SELECT d.name AS dataset, dsi.issue_type, dsi.severity, dsi.issue_detail
        FROM dataset_score_issues dsi
        JOIN dataset_version_scores dvs ON dsi.score_id = dvs.score_id
        JOIN dataset_versions dv ON dvs.version_id = dv.version_id
        JOIN datasets d ON dv.dataset_id = d.dataset_id
        ORDER BY dsi.severity DESC
    """)
    q5 = cur.fetchall()

    cur.close(); conn.close()
    return render_template("queries.html", q1=q1, q2=q2, q3=q3, q4=q4, q5=q5)
if __name__ == "__main__":
    app.run(debug=True)
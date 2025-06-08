# 🧪 Flask Blog

A lightweight, full-stack blogging platform built with **Flask 3 / Python 3.13**.  
Write posts, chat in nested comments, and manage everything from your browser—no WordPress bloat required.

## Features

| Category | Goodies |
|----------|---------|
| **Auth** | 🔑 Secure registration & login (Flask-Login) <br>👑 First registered user auto-promoted to <code>admin</code> |
| **Content** | 📝 Rich-text posts via CKEditor 5 <br>🖼️ Gravatar avatars |
| **Community** | 💬 Threaded / nested comments <br>🗑️ Admins can delete any post or comment |
| **Comms** | 📬 Contact form → Gmail SMTP (env-var creds) |
| **UI / UX** | 🎨 Bootstrap 5 styling <br>🌙 Auto dark-mode (prefers-color-scheme) |
| **Storage** | 🐘 PostgreSQL in prod <br>📝 SQLite fallback for local hacking |

## Tech Stack

- **Python 3.13** · **Flask 3** · **Flask-SQLAlchemy 3 / SQLAlchemy 2**
- **psycopg2-binary** or **psycopg[binary]** (choose your driver)
- **Flask-Login**, **Flask-Bootstrap 5**, **Flask-CKEditor**, **Gravatar**
- Deployed on **Render** (works on Heroku/Fly/Railway too)


## Quick‑start (local)

```bash
git clone https://github.com/your-handle/flask-blog.git
cd flask-blog
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create a **.env** file in the project root:

```env
SECRET_KEY="replace‑me"
MAIL_ADDRESS="your_gmail@gmail.com"
MAIL_APP_PW="16‑char‑app‑password"
# Optional — defaults to SQLite if unset
DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

Run the app:

```bash
python main.py   
```

The first account you register becomes the **admin**.

> **Tip:** comment out `DATABASE_URL` while coding to use the auto‑created `blog.db` SQLite file.

## 🌐 Deployment (Render example)

1. Create a new **Web Service** → **Python**.  
2. Add a **PostgreSQL** database and copy the *external* connection string to `DATABASE_URL`.  
3. Set the same env vars you used locally (`SECRET_KEY`, `MAIL_*`).  
4. Deploy → profit.

## 📂 Project layout

```
.
├── main.py          # Flask app entry‑point
├── forms.py         # WTForms classes
├── templates/       # Jinja2 templates
├── static/          # CSS, JS, images
└── README.md        # ← you are here
```

## 📝 License

MIT — from Angelas course 100 days of code

## 🤝 Contributing

PRs & issues welcome. Open a discussion if you have a feature idea or found a bug.

---

